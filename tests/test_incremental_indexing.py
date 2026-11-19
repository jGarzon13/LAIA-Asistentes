
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

from core.rag.knowledge_base import build_index


class TestIncrementalIndexing(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

        self.root = Path(self.temp.name)

        self.documents_dir = self.root / "documents"
        self.documents_dir.mkdir()

        self.index_file = self.root / "index" / "chunks.json"

        self.document_path = (
            self.documents_dir / "reglamento_prueba.txt"
        )

        self.document_path.write_text(
            "Reglamento ficticio de prueba. "
            "Las evaluaciones son obligatorias.",
            encoding="utf-8"
        )

    def tearDown(self):
        self.temp.cleanup()

    def build(self):
        return build_index(
            documents_dir=self.documents_dir,
            index_file=self.index_file
        )

    def test_first_indexing(self):
        result = self.build()

        self.assertEqual(result["stats"]["new"], 1)
        self.assertEqual(result["stats"]["reused"], 0)
        self.assertEqual(len(result["documents"]), 1)

    def test_reuses_unchanged_document(self):
        first = self.build()

        with patch(
            "core.rag.knowledge_base.load_document"
        ) as mocked_loader:
            second = self.build()

        mocked_loader.assert_not_called()

        self.assertEqual(second["stats"]["reused"], 1)
        self.assertEqual(second["stats"]["new"], 0)

        self.assertEqual(
            first["chunks"],
            second["chunks"]
        )

    def test_modified_document_is_reindexed(self):
        first = self.build()

        self.document_path.write_text(
            "Reglamento ficticio actualizado. "
            "Las evaluaciones incluyen una prueba final.",
            encoding="utf-8"
        )

        second = self.build()

        self.assertEqual(
            second["stats"]["modified"], 1
        )

        self.assertNotEqual(
            first["documents"][0]["id"],
            second["documents"][0]["id"]
        )

    def test_new_document_is_added(self):
        self.build()

        new_path = (
            self.documents_dir / "procedimiento_prueba.txt"
        )

        new_path.write_text(
            "Procedimiento académico de prueba.",
            encoding="utf-8"
        )

        second = self.build()

        self.assertEqual(second["stats"]["new"], 1)
        self.assertEqual(second["stats"]["reused"], 1)
        self.assertEqual(len(second["documents"]), 2)

    def test_deleted_document_is_removed(self):
        self.build()

        self.document_path.unlink()

        second = self.build()

        self.assertEqual(second["stats"]["removed"], 1)
        self.assertEqual(second["documents"], [])
        self.assertEqual(second["chunks"], [])

    def test_failed_document_does_not_corrupt_index(self):
        self.build()

        bad_path = self.documents_dir / "defectuoso.txt"

        bad_path.write_text(
            "Documento que simulará un fallo.",
            encoding="utf-8"
        )

        from core.rag import knowledge_base

        original_loader = knowledge_base.load_document

        def loader_with_failure(path):
            if Path(path).name == "defectuoso.txt":
                raise RuntimeError("Fallo simulado")

            return original_loader(path)

        with patch(
            "core.rag.knowledge_base.load_document",
            side_effect=loader_with_failure
        ):
            result = self.build()

        self.assertEqual(result["stats"]["failed"], 1)
        self.assertEqual(result["stats"]["reused"], 1)
        self.assertEqual(len(result["documents"]), 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertTrue(self.index_file.exists())


if __name__ == "__main__":
    unittest.main()

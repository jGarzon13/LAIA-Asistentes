
import json
import tempfile
import unittest
from pathlib import Path

from core.rag.document_loader import load_document
from core.rag.chunker import chunk_document
from core.rag.knowledge_base import build_index


class TestRAGIngestion(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        self.documents_dir = self.root / "documents"
        self.documents_dir.mkdir()

        self.index_file = self.root / "index" / "chunks.json"

        self.document_path = (
            self.documents_dir / "documento_prueba.txt"
        )

        self.document_path.write_text(
            "Este es un documento ficticio de prueba. "
            "Contiene información académica simulada. "
            "No representa normativa institucional. "
            * 15,
            encoding="utf-8"
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_load_document(self):
        document = load_document(self.document_path)

        self.assertEqual(
            document["filename"],
            "documento_prueba.txt"
        )
        self.assertTrue(document["sections"])

    def test_chunk_document(self):
        document = load_document(self.document_path)

        chunks = chunk_document(
            document,
            max_words=30,
            overlap_words=5
        )

        self.assertGreater(len(chunks), 1)

        for chunk in chunks:
            self.assertLessEqual(
                chunk["word_count"],
                30
            )

    def test_chunk_provenance(self):
        document = load_document(self.document_path)
        chunks = chunk_document(document)

        self.assertEqual(
            chunks[0]["document_id"],
            document["id"]
        )
        self.assertEqual(
            chunks[0]["filename"],
            document["filename"]
        )

    def test_invalid_overlap(self):
        document = load_document(self.document_path)

        with self.assertRaises(ValueError):
            chunk_document(
                document,
                max_words=20,
                overlap_words=20
            )

    def test_build_index(self):
        index = build_index(
            documents_dir=self.documents_dir,
            index_file=self.index_file
        )

        self.assertEqual(len(index["documents"]), 1)
        self.assertGreater(len(index["chunks"]), 0)
        self.assertEqual(len(index["errors"]), 0)
        self.assertTrue(self.index_file.exists())

        saved = json.loads(
            self.index_file.read_text(encoding="utf-8")
        )

        self.assertEqual(
            len(saved["chunks"]),
            len(index["chunks"])
        )


if __name__ == "__main__":
    unittest.main()

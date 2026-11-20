
import json
import tempfile
import unittest
from pathlib import Path

from core.rag.academic_metadata import (
    infer_metadata,
    sync_metadata
)


class TestAcademicMetadata(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.metadata_file = (
            Path(self.temp.name) / "metadata.json"
        )

        self.index = {
            "documents": [
                {
                    "id": "doc001",
                    "sha256": "hash001",
                    "filename": "Reglamento-posgrados.pdf",
                    "source_path": "Reglamento-posgrados.pdf"
                }
            ]
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_infers_postgraduate_regulation(self):
        result = infer_metadata(
            "Reglamento-posgrados.pdf"
        )

        self.assertEqual(result["scope"], "posgrado")
        self.assertEqual(
            result["document_type"], "reglamento"
        )
        self.assertEqual(
            result["validity"], "no_verificada"
        )

    def test_infers_virtual_modality(self):
        result = infer_metadata(
            "Reglamento-pregrado-virtual.pdf"
        )

        self.assertEqual(result["scope"], "pregrado")
        self.assertEqual(result["modality"], "virtual")

    def test_creates_catalog(self):
        catalog = sync_metadata(
            self.index, self.metadata_file
        )

        self.assertEqual(
            catalog["stats"]["created"], 1
        )
        self.assertTrue(self.metadata_file.exists())

    def test_preserves_manual_override(self):
        sync_metadata(self.index, self.metadata_file)

        data = json.loads(
            self.metadata_file.read_text(encoding="utf-8")
        )

        record = data["documents"][
            "Reglamento-posgrados.pdf"
        ]

        record["manual_overrides"] = {
            "scope": "general"
        }
        record["review_status"] = "revisada"

        self.metadata_file.write_text(
            json.dumps(data),
            encoding="utf-8"
        )

        updated = sync_metadata(
            self.index, self.metadata_file
        )

        record = updated["documents"][
            "Reglamento-posgrados.pdf"
        ]

        self.assertEqual(
            record["effective"]["scope"], "general"
        )
        self.assertEqual(
            record["review_status"], "revisada"
        )
        self.assertEqual(
            updated["stats"]["preserved"], 1
        )

    def test_new_version_resets_review(self):
        sync_metadata(self.index, self.metadata_file)

        data = json.loads(
            self.metadata_file.read_text(encoding="utf-8")
        )

        record = data["documents"][
            "Reglamento-posgrados.pdf"
        ]

        record["manual_overrides"] = {
            "scope": "general"
        }
        record["review_status"] = "revisada"

        self.metadata_file.write_text(
            json.dumps(data),
            encoding="utf-8"
        )

        modified_index = {
            "documents": [
                {
                    **self.index["documents"][0],
                    "id": "doc002",
                    "sha256": "hash002"
                }
            ]
        }

        updated = sync_metadata(
            modified_index, self.metadata_file
        )

        record = updated["documents"][
            "Reglamento-posgrados.pdf"
        ]

        self.assertEqual(
            record["manual_overrides"], {}
        )
        self.assertEqual(
            record["review_status"], "pendiente"
        )
        self.assertEqual(
            updated["stats"]["changed"], 1
        )

    def test_removed_document_disappears(self):
        sync_metadata(self.index, self.metadata_file)

        updated = sync_metadata(
            {"documents": []},
            self.metadata_file
        )

        self.assertEqual(updated["documents"], {})
        self.assertEqual(
            updated["stats"]["removed"], 1
        )


if __name__ == "__main__":
    unittest.main()


import json
import tempfile
import unittest
from pathlib import Path

from core.rag.retriever import DocumentRetriever, tokenize


class TestDocumentRetriever(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.index_file = Path(self.temp.name) / "chunks.json"

        chunks = [
            {
                "id": "C001",
                "filename": "reglamento.pdf",
                "page": 2,
                "text": (
                    "Los estudiantes presentan evaluaciones "
                    "académicas durante el semestre."
                ),
                "extraction_method": "ocr",
                "requires_review": True
            },
            {
                "id": "C002",
                "filename": "reglamento.pdf",
                "page": 8,
                "text": (
                    "Los requisitos de graduación incluyen "
                    "aprobar las asignaturas correspondientes."
                ),
                "extraction_method": "text",
                "requires_review": False
            },
            {
                "id": "C003",
                "filename": "documento_ficticio.txt",
                "page": None,
                "text": (
                    "Las solicitudes de transporte se "
                    "presentan en la oficina administrativa."
                ),
                "extraction_method": "text",
                "requires_review": False
            }
        ]

        self.index_file.write_text(
            json.dumps({"chunks": chunks}),
            encoding="utf-8"
        )

        self.retriever = DocumentRetriever(self.index_file)

    def tearDown(self):
        self.temp.cleanup()

    def test_tokenize_accents(self):
        self.assertEqual(
            tokenize("Evaluación académica"),
            ["evaluacion", "academica"]
        )

    def test_relevant_document_first(self):
        results = self.retriever.search(
            "evaluaciones académicas"
        )

        self.assertTrue(results)
        self.assertEqual(results[0]["id"], "C001")

    def test_filter_by_filename(self):
        results = self.retriever.search(
            "solicitudes transporte",
            filename="reglamento.pdf"
        )

        self.assertEqual(results, [])

    def test_no_match(self):
        results = self.retriever.search(
            "astronomía planetaria"
        )

        self.assertEqual(results, [])

    def test_preserves_source_metadata(self):
        results = self.retriever.search(
            "evaluaciones académicas"
        )

        self.assertEqual(results[0]["page"], 2)
        self.assertEqual(
            results[0]["extraction_method"], "ocr"
        )
        self.assertTrue(results[0]["requires_review"])

    def test_invalid_top_k(self):
        with self.assertRaises(ValueError):
            self.retriever.search("evaluaciones", top_k=0)


    def test_accepts_filtered_chunks(self):
        filtered_chunks = [
            chunk for chunk in self.retriever.chunks
            if chunk["filename"] == "reglamento.pdf"
        ]

        filtered_retriever = DocumentRetriever(
            chunks=filtered_chunks
        )

        self.assertEqual(
            len(filtered_retriever.chunks),
            2
        )

        results = filtered_retriever.search(
            "evaluaciones académicas"
        )

        self.assertTrue(results)

        self.assertTrue(
            all(
                result["filename"] == "reglamento.pdf"
                for result in results
            )
        )



if __name__ == "__main__":
    unittest.main()

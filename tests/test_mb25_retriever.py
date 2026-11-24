
import json
import tempfile
import unittest
from pathlib import Path

from core.rag.bm25_retriever import BM25Retriever


class TestBM25Retriever(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.index_file = Path(self.temp.name) / "chunks.json"

        chunks = [
            {
                "id": "C001",
                "filename": "reglamento.pdf",
                "page": 5,
                "text": (
                    "Los estudiantes deben cumplir sus "
                    "deberes y obligaciones académicas."
                ),
                "extraction_method": "ocr",
                "requires_review": True
            },
            {
                "id": "C002",
                "filename": "reglamento.pdf",
                "page": 20,
                "text": (
                    "Las evaluaciones académicas permiten "
                    "valorar el aprendizaje estudiantil."
                ),
                "extraction_method": "text",
                "requires_review": False
            },
            {
                "id": "C003",
                "filename": "otro_documento.txt",
                "page": None,
                "text": (
                    "La biblioteca dispone de libros "
                    "y recursos digitales."
                ),
                "extraction_method": "text",
                "requires_review": False
            }
        ]

        self.index_file.write_text(
            json.dumps({"chunks": chunks}),
            encoding="utf-8"
        )

        self.retriever = BM25Retriever(self.index_file)

    def tearDown(self):
        self.temp.cleanup()

    def test_relevant_result_first(self):
        results = self.retriever.search(
            "evaluaciones académicas"
        )

        self.assertTrue(results)
        self.assertEqual(results[0]["id"], "C002")

    def test_filter_by_filename(self):
        results = self.retriever.search(
            "biblioteca libros",
            filename="reglamento.pdf"
        )

        self.assertEqual(results, [])

    def test_no_match(self):
        results = self.retriever.search(
            "astronomía planetaria"
        )

        self.assertEqual(results, [])

    def test_source_metadata(self):
        results = self.retriever.search(
            "deberes estudiantes"
        )

        self.assertEqual(results[0]["page"], 5)
        self.assertEqual(
            results[0]["extraction_method"], "ocr"
        )
        self.assertTrue(results[0]["requires_review"])

    def test_invalid_top_k(self):
        with self.assertRaises(ValueError):
            self.retriever.search("evaluaciones", top_k=0)

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            BM25Retriever(self.index_file, k1=0)

        with self.assertRaises(ValueError):
            BM25Retriever(self.index_file, b=1.5)

    def test_empty_query(self):
        self.assertEqual(
            self.retriever.search("de la y el"),
            []
        )


if __name__ == "__main__":
    unittest.main()


import unittest

from core.rag.graph.article_detector import (
    detect_article_headings,
    scan_corpus,
)


class TestArticleDetector(unittest.TestCase):

    def test_accented_article(self):
        result = detect_article_headings(
            "ARTÍCULO 2º. La resolución se aplicará en 2027."
        )
        self.assertEqual(result[0]["number"], 2)

    def test_multiple_articles(self):
        result = detect_article_headings(
            "ARTÍCULO 1º. Requisitos. "
            "ARTÍCULO 2º. Aplicación."
        )
        self.assertEqual(
            [item["number"] for item in result],
            [1, 2]
        )

    def test_lowercase_reference_ignored(self):
        result = detect_article_headings(
            "De acuerdo con el artículo 75 de la resolución."
        )
        self.assertEqual(result, [])

    def test_fictitious_document_excluded(self):
        chunks = [{
            "id": "TEST-1",
            "filename": "procedimiento_academico_ficticio.txt",
            "page": 1,
            "text": "ARTÍCULO 1. Documento de prueba.",
        }]

        result = scan_corpus(chunks)
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()


import unittest

from core.rag.graph.article_indexer import (
    build_article_index,
)


def make_chunk(
    chunk_id,
    text,
    filename="reglamento.pdf",
    review=False,
):
    return {
        "id": chunk_id,
        "document_id": "DOC-1",
        "filename": filename,
        "page": 1,
        "text": text,
        "requires_review": review,
    }


class TestArticleIndexer(unittest.TestCase):

    def test_detects_article(self):
        data = build_article_index([
            make_chunk(
                "C1",
                "ARTÍCULO 1º. Requisitos."
            )
        ])

        candidate = data[0]["candidates"][0]

        self.assertEqual(
            candidate["detected_number"], 1
        )

    def test_groups_duplicate_detection(self):
        data = build_article_index([
            make_chunk("C1", "ARTÍCULO 2º. Inicio."),
            make_chunk("C2", "ARTÍCULO 2º. Inicio."),
        ])

        self.assertEqual(
            len(data[0]["candidates"]), 1
        )

        self.assertEqual(
            len(data[0]["candidates"][0]["evidence"]),
            2,
        )

    def test_preserves_ocr_proposal(self):
        data = build_article_index([
            make_chunk(
                "C1",
                "ARTÍCULO 109: Admisión.",
                review=True,
            )
        ])

        candidate = data[0]["candidates"][0]

        self.assertEqual(
            candidate["proposed_numbers"], [10]
        )

        self.assertEqual(
            candidate["status"],
            "requires_verification",
        )

    def test_excludes_fictitious_document(self):
        data = build_article_index([
            make_chunk(
                "C1",
                "ARTÍCULO 1. Prueba.",
                filename=(
                    "procedimiento_academico_ficticio.txt"
                ),
            )
        ])

        self.assertEqual(data, [])


if __name__ == "__main__":
    unittest.main()


import unittest

from core.rag.graph.evidence_retriever import EvidenceRetriever
from core.rag.graph.knowledge_graph import SOURCE


def make_chunk(chunk_id, filename, text, page=1):
    return {
        "id": chunk_id,
        "document_id": "test-document",
        "filename": filename,
        "page": page,
        "text": text,
        "requires_review": False,
    }


class TestEvidenceRetriever(unittest.TestCase):

    def setUp(self):
        self.chunks = [
            make_chunk(
                "C0001", SOURCE,
                "ARTÍCULO 1º. Para graduarse se requieren créditos."
            ),
            make_chunk(
                "C0002", SOURCE,
                "El estudiante debe presentar Saber Pro."
            ),
            make_chunk(
                "C0003", SOURCE,
                "ARTÍCULO 2º. Se aplicará desde 2027."
            ),
            make_chunk(
                "C0004", "otro-documento.pdf",
                "ARTÍCULO 1º. Información de otro documento."
            ),
        ]

        self.retriever = EvidenceRetriever(
            chunks=self.chunks
        )

    def test_recovers_original_evidence(self):
        result = self.retriever.search(
            "¿Qué debo hacer para graduarme?",
            scope="pregrado"
        )

        self.assertEqual(result["status"], "ok")
        self.assertGreater(len(result["evidence"]), 0)

        combined = " ".join(
            chunk["text"]
            for chunk in result["evidence"]
        )

        self.assertIn("Saber Pro", combined)
        self.assertIn("2027", combined)

    def test_does_not_mix_documents(self):
        result = self.retriever.search(
            "¿Qué debo hacer para graduarme?",
            scope="pregrado"
        )

        self.assertTrue(
            all(
                chunk["filename"] == SOURCE
                for chunk in result["evidence"]
            )
        )

    def test_removes_duplicate_chunks(self):
        result = self.retriever.search(
            "¿Qué debo hacer para graduarme?",
            scope="pregrado"
        )

        ids = [
            chunk["id"]
            for chunk in result["evidence"]
        ]

        self.assertEqual(len(ids), len(set(ids)))

    def test_reports_missing_article(self):
        retriever = EvidenceRetriever(
            chunks=self.chunks[:2]
        )

        result = retriever.search(
            "¿Qué debo hacer para graduarme?",
            scope="pregrado"
        )

        self.assertEqual(
            result["status"], "partial_evidence"
        )
        self.assertTrue(result["missing_articles"])

    def test_unsupported_scope(self):
        result = self.retriever.search(
            "¿Cómo me gradúo de posgrado?",
            scope="posgrado"
        )

        self.assertEqual(
            result["status"], "unsupported_scope"
        )
        self.assertEqual(result["evidence"], [])


if __name__ == "__main__":
    unittest.main()

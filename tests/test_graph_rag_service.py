
import unittest

from core.rag.graph.graph_rag_service import GraphRAGService


class FakeEvidenceRetriever:

    def search(self, question, scope="pregrado"):
        if scope != "pregrado":
            return {
                "status": "unsupported_scope",
                "facts": [],
                "evidence": [],
            }

        return {
            "status": "ok",
            "facts": [],
            "evidence": [{
                "id": "TEST-C0001",
                "filename": "resolucion-prueba.pdf",
                "page": 1,
                "text": (
                    "ARTÍCULO 2. Los requisitos se aplican "
                    "desde el primer periodo académico de 2027."
                ),
                "requires_review": False,
            }],
        }


class TestGraphRAGService(unittest.TestCase):

    def setUp(self):
        self.service = GraphRAGService(
            evidence_retriever=FakeEvidenceRetriever()
        )

    def test_prepare_returns_evidence(self):
        result = self.service.prepare(
            "¿Desde cuándo aplican los requisitos?"
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(len(result["retrieved_contexts"]), 1)

    def test_prompt_includes_original_document(self):
        result = self.service.prepare(
            "¿Desde cuándo aplican los requisitos?"
        )

        self.assertIn("2027", result["prompt"])
        self.assertIn("[FUENTE 1]", result["prompt"])
        self.assertIn("resolucion-prueba.pdf", result["prompt"])

    def test_does_not_call_llm_without_generator(self):
        result = self.service.ask(
            "¿Desde cuándo aplican los requisitos?"
        )

        self.assertEqual(
            result["status"], "generator_not_configured"
        )
        self.assertIsNone(result["answer"])

    def test_supports_injected_generator(self):
        prompts = []

        def fake_generator(prompt):
            prompts.append(prompt)
            return "Los requisitos se aplican desde 2027 [FUENTE 1]."

        service = GraphRAGService(
            evidence_retriever=FakeEvidenceRetriever(),
            generator=fake_generator
        )

        result = service.ask(
            "¿Desde cuándo aplican los requisitos?"
        )

        self.assertEqual(len(prompts), 1)
        self.assertIn("2027", result["answer"])

    def test_unsupported_scope_does_not_generate(self):
        result = self.service.ask(
            "¿Cómo me gradúo de posgrado?",
            scope="posgrado"
        )

        self.assertEqual(result["status"], "unsupported_scope")
        self.assertIsNone(result["answer"])


if __name__ == "__main__":
    unittest.main()

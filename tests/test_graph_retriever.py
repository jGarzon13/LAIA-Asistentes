
import unittest

from core.rag.graph.graph_retriever import GraphRetriever


class TestGraphRetriever(unittest.TestCase):

    def setUp(self):
        self.retriever = GraphRetriever()

    def test_graduation_retrieves_requirements(self):
        result = self.retriever.search(
            "¿Qué debo hacer para graduarme?",
            scope="pregrado"
        )

        self.assertEqual(result["status"], "ok")

        destinations = {
            fact["destination"]
            for fact in result["facts"]
        }

        self.assertIn(
            "Aprobar créditos del plan de estudios",
            destinations
        )

        self.assertIn(
            "Primer periodo académico de 2027",
            destinations
        )

    def test_saber_pro_retrieves_alternatives(self):
        result = self.retriever.search(
            "¿Qué pasa si no alcanzo el percentil 40?",
            scope="pregrado"
        )

        destinations = {
            fact["destination"]
            for fact in result["facts"]
        }

        self.assertIn(
            "Presentar nuevamente Saber Pro",
            destinations
        )

    def test_posgrado_is_not_supported(self):
        result = self.retriever.search(
            "¿Cómo puedo graduarme de posgrado?",
            scope="posgrado"
        )

        self.assertEqual(
            result["status"], "unsupported_scope"
        )
        self.assertEqual(result["facts"], [])

    def test_unknown_question_has_no_match(self):
        result = self.retriever.search(
            "¿Qué actividades deportivas hay?",
            scope="pregrado"
        )

        self.assertEqual(result["status"], "no_match")

    def test_facts_include_provenance(self):
        result = self.retriever.search(
            "¿Desde cuándo aplica la resolución?",
            scope="pregrado"
        )

        self.assertEqual(result["status"], "ok")

        for fact in result["facts"]:
            self.assertTrue(fact["source"])
            self.assertTrue(fact["article"])
            self.assertIsNotNone(fact["page"])


if __name__ == "__main__":
    unittest.main()

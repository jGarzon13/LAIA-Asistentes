
import unittest

from core.rag.graph.knowledge_graph import (
    build_academic_graph,
    get_document_facts
)


class TestAcademicGraph(unittest.TestCase):

    def setUp(self):
        self.graph = build_academic_graph()

    def test_graph_structure(self):
        self.assertEqual(
            self.graph.number_of_nodes(), 10
        )
        self.assertEqual(
            self.graph.number_of_edges(), 9
        )

    def test_temporal_application(self):
        self.assertTrue(
            self.graph.has_edge(
                "art_2", "aplicacion_2027"
            )
        )

    def test_saber_pro_conditions(self):
        self.assertTrue(
            self.graph.has_edge(
                "saber_pro", "percentil_40"
            )
        )

        self.assertTrue(
            self.graph.has_edge(
                "percentil_40",
                "ruta_fortalecimiento"
            )
        )

    def test_facts_keep_sources(self):
        facts = get_document_facts(
            self.graph, "res_6865"
        )

        self.assertEqual(len(facts), 9)

        self.assertTrue(
            all(
                fact["source"]
                and fact["article"]
                and fact["page"]
                for fact in facts
            )
        )

    def test_unknown_document(self):
        with self.assertRaises(ValueError):
            get_document_facts(
                self.graph, "documento_inexistente"
            )


if __name__ == "__main__":
    unittest.main()

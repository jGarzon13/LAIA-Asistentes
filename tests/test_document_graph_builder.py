
import unittest

from core.rag.graph.document_graph_builder import (
    build_document_graph
)


class TestDocumentGraphBuilder(unittest.TestCase):

    def setUp(self):
        self.chunks = [
            {
                "id": "A-C0001",
                "document_id": "A",
                "filename": "reglamento.pdf",
                "page": 1,
                "text": "ARTÍCULO 1. Requisitos.",
                "requires_review": False,
            },
            {
                "id": "A-C0002",
                "document_id": "A",
                "filename": "reglamento.pdf",
                "page": 2,
                "text": "Continúan los requisitos.",
                "requires_review": True,
            },
            {
                "id": "F-C0001",
                "document_id": "F",
                "filename": "procedimiento_academico_ficticio.txt",
                "page": 1,
                "text": "Documento de prueba",
                "requires_review": False,
            },
        ]
        self.graph = build_document_graph(self.chunks)

    def test_document_node(self):
        self.assertIn("doc:A", self.graph)

    def test_page_relation(self):
        self.assertEqual(
            self.graph.edges["doc:A", "page:A:1"]["relation"],
            "HAS_PAGE",
        )

    def test_next_chunk_across_pages(self):
        self.assertEqual(
            self.graph.edges[
                "chunk:A-C0001", "chunk:A-C0002"
            ]["relation"],
            "NEXT_CHUNK",
        )

    def test_review_flag(self):
        self.assertTrue(
            self.graph.nodes["chunk:A-C0002"]["requires_review"]
        )

    def test_excludes_fictitious_document(self):
        self.assertNotIn("doc:F", self.graph)
        self.assertNotIn("chunk:F-C0001", self.graph)


if __name__ == "__main__":
    unittest.main()

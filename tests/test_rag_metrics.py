
import unittest

from evaluation.rag_metrics import evaluate_results


class TestRAGMetrics(unittest.TestCase):

    def setUp(self):
        self.results = [
            {"filename": "reglamento.pdf", "page": 4},
            {"filename": "reglamento.pdf", "page": 22},
            {"filename": "reglamento.pdf", "page": 18}
        ]

    def test_first_relevant_rank(self):
        metrics = evaluate_results(
            self.results,
            "reglamento.pdf",
            [22]
        )

        self.assertEqual(
            metrics["first_relevant_rank"], 2
        )
        self.assertEqual(
            metrics["reciprocal_rank"], 0.5
        )

    def test_relevant_page_not_found(self):
        metrics = evaluate_results(
            self.results,
            "reglamento.pdf",
            [25]
        )

        self.assertEqual(metrics["hit"], 0)
        self.assertEqual(metrics["reciprocal_rank"], 0.0)
        self.assertIsNone(metrics["first_relevant_rank"])

    def test_wrong_document_not_relevant(self):
        metrics = evaluate_results(
            self.results,
            "otro_documento.pdf",
            [22]
        )

        self.assertEqual(metrics["hit"], 0)


if __name__ == "__main__":
    unittest.main()

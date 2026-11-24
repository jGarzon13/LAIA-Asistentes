
import unittest

from core.rag.graph.article_heading_classifier import (
    classify_occurrence,
)


class TestArticleHeadingClassifier(unittest.TestCase):

    def test_regular_heading(self):
        text = "ARTÍCULO 2º. REQUISITOS DE GRADO."

        result = classify_occurrence(
            text, 0, 2
        )

        self.assertEqual(
            result["classification"],
            "heading_candidate",
        )

    def test_normative_reference(self):
        text = (
            "La resolución modifica el "
            "ARTÍCULO 75º. del reglamento."
        )

        result = classify_occurrence(
            text,
            text.index("ARTÍCULO"),
            75,
        )

        self.assertEqual(
            result["classification"],
            "reference_candidate",
        )

    def test_ocr_suspected(self):
        text = "ARTÍCULO 109: CONCEPTO DE ADMISIÓN."

        result = classify_occurrence(
            text, 0, 109,
            proposed_numbers=[10],
            requires_review=True,
        )

        self.assertEqual(
            result["classification"],
            "ocr_suspected",
        )

    def test_ambiguous_text(self):
        text = "ARTÍCULO 12."

        result = classify_occurrence(
            text, 0, 12
        )

        self.assertEqual(
            result["classification"],
            "ambiguous",
        )

    def test_missing_position(self):
        text = "ARTÍCULO 3º. REQUISITOS."

        result = classify_occurrence(
            text, 100, 3
        )

        self.assertEqual(
            result["classification"],
            "ambiguous",
        )


if __name__ == "__main__":
    unittest.main()

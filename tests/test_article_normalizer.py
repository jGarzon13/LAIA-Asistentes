
import unittest

from core.rag.graph.article_normalizer import (
    review_article_number,
)


class TestArticleNormalizer(unittest.TestCase):

    def test_suggests_ocr_nine_correction(self):
        result = review_article_number(109, True)

        self.assertEqual(result.proposed, 10)
        self.assertEqual(
            result.status, "requires_verification"
        )

    def test_suggests_ocr_zero_correction(self):
        result = review_article_number(120, True)

        self.assertEqual(result.proposed, 12)

    def test_preserves_unflagged_number(self):
        result = review_article_number(109, False)

        self.assertIsNone(result.proposed)
        self.assertEqual(result.detected, 109)

    def test_does_not_modify_regular_number(self):
        result = review_article_number(54, True)

        self.assertIsNone(result.proposed)
        self.assertEqual(result.detected, 54)

    def test_preserves_two_digit_ocr_numbers(self):
        for number in (10, 20, 49):
            result = review_article_number(
                number,
                requires_review=True
            )

            self.assertIsNone(result.proposed)
            self.assertEqual(
                result.status,
                "original_unverified"
            )


if __name__ == "__main__":
    unittest.main()

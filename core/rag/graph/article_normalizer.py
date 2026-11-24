
"""Propuestas conservadoras de corrección para números de artículos OCR."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ArticleNumberReview:
    detected: int
    proposed: int | None
    status: str
    reason: str


def review_article_number(
    number: int,
    requires_review: bool = False,
) -> ArticleNumberReview:
    """
    Sugiere correcciones; nunca las valida automáticamente.

    Una propuesta no debe utilizarse como número definitivo
    de artículo sin una comprobación adicional.
    """

    if not requires_review:
        return ArticleNumberReview(
            detected=number,
            proposed=None,
            status="original",
            reason="Sin indicador de revisión OCR",
        )

    value = str(number)

    if len(value) >= 3 and value.endswith(("9", "0")):
        candidate = int(value[:-1])

        if candidate >= 1:
            return ArticleNumberReview(
                detected=number,
                proposed=candidate,
                status="requires_verification",
                reason=(
                    "Posible símbolo ordinal reconocido "
                    "como 9 o 0"
                ),
            )

    return ArticleNumberReview(
        detected=number,
        proposed=None,
        status="original_unverified",
        reason="Número procedente de texto marcado para revisión",
    )

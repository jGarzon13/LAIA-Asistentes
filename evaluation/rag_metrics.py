
def relevant_rank(
    results: list[dict],
    filename: str,
    relevant_pages: list[int]
) -> int | None:
    """Posición del primer resultado de una página relevante."""

    for position, result in enumerate(results, start=1):
        if (
            result["filename"] == filename
            and result["page"] in relevant_pages
        ):
            return position

    return None


def evaluate_results(
    results: list[dict],
    filename: str,
    relevant_pages: list[int]
) -> dict:
    """Calcula Hit@K y Reciprocal Rank."""

    rank = relevant_rank(
        results,
        filename,
        relevant_pages
    )

    return {
        "hit": int(rank is not None),
        "reciprocal_rank": (
            1.0 / rank if rank is not None else 0.0
        ),
        "first_relevant_rank": rank
    }

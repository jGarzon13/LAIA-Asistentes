
import json
import math
from collections import Counter
from pathlib import Path

from core.rag.retriever import INDEX_FILE, tokenize


class BM25Retriever:
    """Recuperador léxico basado en Okapi BM25."""

    def __init__(
        self,
        index_file: str | Path = INDEX_FILE,
        k1: float = 1.5,
        b: float = 0.75
    ):
        if k1 <= 0:
            raise ValueError("k1 debe ser positivo.")

        if not 0 <= b <= 1:
            raise ValueError("b debe estar entre 0 y 1.")

        self.index_file = Path(index_file)
        self.k1 = k1
        self.b = b

        if not self.index_file.is_file():
            raise FileNotFoundError(
                f"No se encontró el índice: {self.index_file}"
            )

        data = json.loads(
            self.index_file.read_text(encoding="utf-8")
        )

        self.chunks = data.get("chunks", [])

    def search(
        self,
        query: str,
        top_k: int = 5,
        filename: str | None = None,
        min_score: float = 0.0
    ) -> list[dict]:
        """Busca los fragmentos con mayor puntuación BM25."""

        if top_k <= 0:
            raise ValueError("top_k debe ser positivo.")

        if min_score < 0:
            raise ValueError("min_score no puede ser negativo.")

        query_terms = set(tokenize(query))

        if not query_terms:
            return []

        candidates = [
            chunk for chunk in self.chunks
            if filename is None
            or chunk["filename"] == filename
        ]

        if not candidates:
            return []

        tokenized = [
            tokenize(chunk["text"])
            for chunk in candidates
        ]

        total_docs = len(tokenized)

        avg_length = (
            sum(len(terms) for terms in tokenized)
            / total_docs
        )

        document_frequency = Counter()

        for terms in tokenized:
            document_frequency.update(set(terms))

        results = []

        for chunk, terms in zip(candidates, tokenized):
            if not terms:
                continue

            frequencies = Counter(terms)
            document_length = len(terms)
            score = 0.0
            matched_terms = []

            for term in query_terms:
                frequency = frequencies.get(term, 0)

                if frequency == 0:
                    continue

                matched_terms.append(term)

                df = document_frequency[term]

                idf = math.log(
                    1 + (
                        total_docs - df + 0.5
                    ) / (df + 0.5)
                )

                normalization = (
                    1 - self.b
                    + self.b * document_length / avg_length
                )

                term_score = (
                    idf
                    * frequency * (self.k1 + 1)
                    / (
                        frequency
                        + self.k1 * normalization
                    )
                )

                score += term_score

            if score <= 0 or score < min_score:
                continue

            results.append({
                "id": chunk["id"],
                "filename": chunk["filename"],
                "page": chunk.get("page"),
                "text": chunk["text"],
                "score": round(score, 4),
                "matched_terms": sorted(matched_terms),
                "extraction_method": chunk.get(
                    "extraction_method", "text"
                ),
                "requires_review": chunk.get(
                    "requires_review", False
                )
            })

        results.sort(
            key=lambda item: (-item["score"], item["id"])
        )

        return results[:top_k]

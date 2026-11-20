
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX_FILE = ROOT / "knowledge" / "index" / "chunks.json"

STOPWORDS = {
    "a", "al", "ante", "como", "con", "cual", "cuales",
    "de", "del", "el", "en", "es", "esta", "este",
    "hay", "la", "las", "lo", "los", "para", "por",
    "que", "se", "segun", "su", "sus", "un", "una",
    "y", "o", "sobre", "puede", "pueden"
}


def tokenize(text: str) -> list[str]:
    """Normaliza tildes y obtiene términos relevantes."""
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(
        char for char in normalized
        if not unicodedata.combining(char)
    ).lower()

    words = re.findall(r"[a-z0-9]+", normalized)

    return [
        word for word in words
        if word not in STOPWORDS and len(word) > 1
    ]


class DocumentRetriever:
    
    def __init__(
        self,
        index_file: str | Path = INDEX_FILE,
        chunks: list[dict] | None = None
    ):
        self.index_file = Path(index_file)

        # Si recibimos fragmentos filtrados por ámbito,
        # trabajamos directamente con ellos.
        if chunks is not None:
            self.chunks = list(chunks)
            return

        # Si no recibimos fragmentos, usamos el índice
        # documental completo, como antes.
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
        """Recupera fragmentos mediante TF-IDF y coseno."""

        if top_k <= 0:
            raise ValueError("top_k debe ser positivo.")

        if not 0 <= min_score <= 1:
            raise ValueError("min_score debe estar entre 0 y 1.")

        query_terms = tokenize(query)

        if not query_terms:
            return []

        candidates = [
            chunk for chunk in self.chunks
            if filename is None
            or chunk["filename"] == filename
        ]

        if not candidates:
            return []

        doc_terms = [
            tokenize(chunk["text"])
            for chunk in candidates
        ]

        total_docs = len(doc_terms)

        document_frequency = Counter()

        for terms in doc_terms:
            document_frequency.update(set(terms))

        def idf(term: str) -> float:
            return math.log(
                (total_docs + 1)
                / (document_frequency.get(term, 0) + 1)
            ) + 1

        query_counts = Counter(query_terms)
        query_vector = {
            term: count * idf(term)
            for term, count in query_counts.items()
        }

        query_norm = math.sqrt(
            sum(value ** 2 for value in query_vector.values())
        )

        results = []

        for chunk, terms in zip(candidates, doc_terms):
            counts = Counter(terms)

            doc_vector = {
                term: count * idf(term)
                for term, count in counts.items()
            }

            doc_norm = math.sqrt(
                sum(value ** 2 for value in doc_vector.values())
            )

            if query_norm == 0 or doc_norm == 0:
                continue

            common_terms = set(query_vector) & set(doc_vector)

            if not common_terms:
                continue

            dot_product = sum(
                query_vector[term] * doc_vector[term]
                for term in common_terms
            )

            score = dot_product / (query_norm * doc_norm)

            if score <= 0 or score < min_score:
                continue

            results.append({
                "id": chunk["id"],
                "filename": chunk["filename"],
                "page": chunk.get("page"),
                "text": chunk["text"],
                "score": round(score, 4),
                "matched_terms": sorted(common_terms),
                "extraction_method": chunk.get(
                    "extraction_method", "text"
                ),
                "requires_review": chunk.get(
                    "requires_review", False
                )
            })

        results.sort(
            key=lambda result: result["score"],
            reverse=True
        )

        return results[:top_k]

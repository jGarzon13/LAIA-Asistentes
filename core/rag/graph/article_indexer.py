
"""Índice auditable de candidatos de artículos para LAIA."""

import json
from collections import Counter
from pathlib import Path

from core.rag.graph.article_detector import (
    detect_article_headings,
)
from core.rag.graph.article_normalizer import (
    review_article_number,
)


ROOT = Path(__file__).resolve().parents[3]
INDEX_FILE = ROOT / "knowledge/index/chunks.json"
OUTPUT_FILE = ROOT / "knowledge/graph/article_index.json"

EXCLUDED = {"procedimiento_academico_ficticio.txt"}


def build_article_index(chunks):
    """Agrupa detecciones y conserva todas sus evidencias."""

    documents = {}

    for chunk in chunks:
        filename = chunk["filename"]

        if filename.casefold() in EXCLUDED:
            continue

        document_id = chunk["document_id"]

        doc = documents.setdefault(
            document_id,
            {
                "filename": filename,
                "candidates": {},
            },
        )

        text = chunk.get("text", "")
        flagged = bool(chunk.get("requires_review", False))

        for match in detect_article_headings(text):
            number = match["number"]

            review = review_article_number(
                number,
                requires_review=flagged,
            )

            # Se agrupan detecciones idénticas, pero no se
            # confirman automáticamente como artículos reales.
            key = str(number)

            candidate = doc["candidates"].setdefault(
                key,
                {
                    "detected_number": number,
                    "status": "candidate",
                    "proposed_numbers": [],
                    "evidence": [],
                },
            )

            if review.proposed is not None:
                proposal = review.proposed

                if proposal not in candidate["proposed_numbers"]:
                    candidate["proposed_numbers"].append(
                        proposal
                    )

            evidence_key = (
                chunk["id"],
                match["position"],
            )

            existing = {
                (e["chunk_id"], e["position"])
                for e in candidate["evidence"]
            }

            if evidence_key not in existing:
                candidate["evidence"].append({
                    "chunk_id": chunk["id"],
                    "page": chunk["page"],
                    "position": match["position"],
                    "requires_review": flagged,
                    "review_status": review.status,
                    "reason": review.reason,
                })

    result = []

    for document_id, document in documents.items():
        candidates = list(
            document["candidates"].values()
        )

        for candidate in candidates:
            if candidate["proposed_numbers"]:
                candidate["status"] = (
                    "requires_verification"
                )
            elif any(
                evidence["requires_review"]
                for evidence in candidate["evidence"]
            ):
                candidate["status"] = (
                    "ocr_unverified"
                )

        candidates.sort(
            key=lambda item: item["detected_number"]
        )

        result.append({
            "document_id": document_id,
            "filename": document["filename"],
            "candidates": candidates,
        })

    return result


def save_index(data, path=OUTPUT_FILE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp = path.with_suffix(".json.tmp")

    try:
        temp.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "type": "article_candidates",
                    "documents": data,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()


def main():
    source = json.loads(
        INDEX_FILE.read_text(encoding="utf-8")
    )

    documents = build_article_index(
        source["chunks"]
    )

    save_index(documents)

    counts = Counter(
        candidate["status"]
        for document in documents
        for candidate in document["candidates"]
    )

    print("\nLAIA - Índice de candidatos de artículos")
    print("Documentos:", len(documents))

    print(
        "Candidatos únicos por documento y número:",
        sum(
            len(doc["candidates"])
            for doc in documents
        ),
    )

    print("\nESTADOS:")
    for status, count in counts.items():
        print(f"- {status}: {count}")

    print("\nArchivo generado:", OUTPUT_FILE)


if __name__ == "__main__":
    main()

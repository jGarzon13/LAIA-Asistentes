
import json
from datetime import datetime, timezone
from pathlib import Path

from core.rag.retriever import DocumentRetriever
from evaluation.rag_metrics import evaluate_results


ROOT = Path(__file__).resolve().parents[1]

CASES_FILE = ROOT / "evaluation" / "rag_cases.json"
OUTPUT_FILE = (
    ROOT / "docs" / "evaluaciones"
    / "rag_retrieval_baseline.json"
)


def main():
    cases = json.loads(
        CASES_FILE.read_text(encoding="utf-8")
    )

    if not cases:
        raise ValueError("No hay casos RAG para evaluar.")

    retriever = DocumentRetriever()
    top_k = 3
    results = []

    print("\nLAIA - Evaluación de recuperación documental")
    print("=" * 55)

    for case in cases:
        retrieved = retriever.search(
            query=case["question"],
            filename=case["filename"],
            top_k=top_k
        )

        metrics = evaluate_results(
            retrieved,
            case["filename"],
            case["relevant_pages"]
        )

        record = {
            "id": case["id"],
            "question": case["question"],
            "expected_pages": case["relevant_pages"],
            "retrieved_pages": [
                item["page"] for item in retrieved
            ],
            "scores": [
                item["score"] for item in retrieved
            ],
            **metrics
        }

        results.append(record)

        print(f"\n{case['id']}: {case['question']}")
        print(f"Páginas: {record['retrieved_pages']}")
        print(f"Primer acierto: {metrics['first_relevant_rank']}")

    total = len(results)

    hit_at_k = sum(
        item["hit"] for item in results
    ) / total

    mrr_at_k = sum(
        item["reciprocal_rank"] for item in results
    ) / total

    report = {
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "retriever": "TF-IDF manual + cosine",
        "top_k": top_k,
        "total_cases": total,
        "hit_at_k": round(hit_at_k, 4),
        "mrr_at_k": round(mrr_at_k, 4),
        "cases": results
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("\n" + "=" * 55)
    print(f"Casos evaluados: {total}")
    print(f"Hit@{top_k}: {hit_at_k:.2%}")
    print(f"MRR@{top_k}: {mrr_at_k:.4f}")
    print(f"Reporte: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

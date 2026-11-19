
import json
from datetime import datetime, timezone
from pathlib import Path

from core.rag.retriever import DocumentRetriever
from core.rag.bm25_retriever import BM25Retriever
from evaluation.rag_metrics import evaluate_results


ROOT = Path(__file__).resolve().parents[1]

CASES_FILE = ROOT / "evaluation" / "rag_cases.json"
OUTPUT_FILE = (
    ROOT / "docs" / "evaluaciones"
    / "rag_retrieval_comparison.json"
)


def evaluate_retriever(name, retriever, cases, top_k=3):
    records = []

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

        records.append({
            "id": case["id"],
            "question": case["question"],
            "retrieved_pages": [
                item["page"] for item in retrieved
            ],
            "retrieved_ids": [
                item["id"] for item in retrieved
            ],
            "scores": [
                item["score"] for item in retrieved
            ],
            **metrics
        })

    count = len(records)

    return {
        "algorithm": name,
        "hit_at_k": sum(
            item["hit"] for item in records
        ) / count,
        "mrr_at_k": sum(
            item["reciprocal_rank"] for item in records
        ) / count,
        "cases": records
    }


def main():
    cases = json.loads(
        CASES_FILE.read_text(encoding="utf-8")
    )

    if not cases:
        raise ValueError("No hay casos para evaluar.")

    top_k = 3

    algorithms = {
        "TF-IDF": DocumentRetriever(),
        "BM25": BM25Retriever()
    }

    report = {
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "top_k": top_k,
        "total_cases": len(cases),
        "results": {}
    }

    print("\nLAIA - Comparación de recuperadores")
    print("=" * 55)

    for name, retriever in algorithms.items():
        evaluation = evaluate_retriever(
            name,
            retriever,
            cases,
            top_k
        )

        report["results"][name] = evaluation

        print(f"\n{name}")
        print(f"Hit@{top_k}: {evaluation['hit_at_k']:.2%}")
        print(f"MRR@{top_k}: {evaluation['mrr_at_k']:.4f}")

        for case in evaluation["cases"]:
            print(
                f"  {case['id']}: "
                f"páginas {case['retrieved_pages']} "
                f"| primer acierto "
                f"{case['first_relevant_rank']}"
            )

    tfidf = report["results"]["TF-IDF"]
    bm25 = report["results"]["BM25"]

    difference = (
        bm25["mrr_at_k"] - tfidf["mrr_at_k"]
    )

    print("\n" + "=" * 55)
    print(f"Diferencia MRR@{top_k} (BM25 - TF-IDF): {difference:+.4f}")

    if difference > 0:
        print("BM25 obtuvo mejor MRR en esta muestra.")
    elif difference < 0:
        print("TF-IDF obtuvo mejor MRR en esta muestra.")
    else:
        print("Ambos obtuvieron el mismo MRR en esta muestra.")

    OUTPUT_FILE.parent.mkdir(
        parents=True, exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(f"\nReporte: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

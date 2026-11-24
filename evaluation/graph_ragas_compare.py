
"""Evalúa GraphRAG reutilizando el evaluador Ragas de LAIA."""

import argparse
import asyncio
import json
from pathlib import Path

from evaluation import ragas_four_metrics as evaluator


ROOT = Path(__file__).resolve().parents[1]

GRAPH_INPUT = (
    ROOT / "evaluation/results/graph_first_run.json"
)

GRAPH_OUTPUT = (
    ROOT / "evaluation/results/graph_ragas_metrics.json"
)

BASELINE_OUTPUT = (
    ROOT / "evaluation/results/ragas_four_metrics.json"
)

METRICS = (
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
)


def read_scores(path, case_id):
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))

    cases = data.get("cases", {})
    case = cases.get(case_id, {})

    # Admite también resultados guardados directamente
    # por identificador del caso.
    if not case:
        case = data.get(case_id, {})

    metrics = case.get("metrics", {})
    scores = {}

    for name in METRICS:
        entry = metrics.get(name, {})
        if isinstance(entry, dict):
            scores[name] = entry.get("score")
        elif isinstance(entry, (int, float)):
            scores[name] = float(entry)
        else:
            scores[name] = None

    return scores


def show_comparison(case_id):
    baseline = read_scores(BASELINE_OUTPUT, case_id)
    graph = read_scores(GRAPH_OUTPUT, case_id)

    print("\nCOMPARACIÓN EXPERIMENTAL")
    print("Caso:", case_id)
    print("-" * 65)

    for name in METRICS:
        a = baseline.get(name)
        b = graph.get(name)

        a_text = "Pendiente" if a is None else f"{a:.4f}"
        b_text = "Pendiente" if b is None else f"{b:.4f}"

        print(f"{name:20} Naive={a_text:12} Graph={b_text}")

    print("\nLos resultados pendientes no equivalen a cero.")


async def evaluate(case_id, metric):
    if not GRAPH_INPUT.exists():
        raise FileNotFoundError(
            "Primero ejecuta evaluation.graph_first_answer"
        )

    # El evaluador original utiliza rutas configurables
    # como constantes del módulo. Las sustituimos únicamente
    # en este proceso, sin editar sus archivos.
    original_input = evaluator.INPUT_FILE
    original_output = evaluator.OUTPUT_FILE

    try:
        evaluator.INPUT_FILE = GRAPH_INPUT
        evaluator.OUTPUT_FILE = GRAPH_OUTPUT

        await evaluator.main(case_id, metric)

    finally:
        evaluator.INPUT_FILE = original_input
        evaluator.OUTPUT_FILE = original_output


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--case", default="PRE-01"
    )

    parser.add_argument(
        "--metric",
        choices=METRICS,
        help="Métrica a evaluar",
    )

    args = parser.parse_args()

    if args.metric:
        asyncio.run(evaluate(args.case, args.metric))

    show_comparison(args.case)


if __name__ == "__main__":
    main()

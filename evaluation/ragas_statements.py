
import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from instructor import Mode
from openai import AsyncOpenAI

from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness


ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT / "evaluation" / "results"
    / "ragas_first_run.json"
)

OUTPUT_FILE = (
    ROOT / "evaluation" / "results"
    / "ragas_statements_pre01.json"
)

JUDGE_MODEL = "openai/gpt-oss-20b"


def extract_statements(answer):
    """Extrae los puntos numerados de una respuesta."""
    statements = []

    pattern = re.compile(r"^\s*(\d+)\.\s+(.+)$")

    for line in answer.splitlines():
        match = pattern.match(line)

        if match:
            statements.append({
                "number": int(match.group(1)),
                "text": match.group(2).strip()
            })

    return statements


def save_results(data):
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary = OUTPUT_FILE.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    temporary.replace(OUTPUT_FILE)


async def main():
    load_dotenv(ROOT / ".env")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"No existe: {INPUT_FILE}"
        )

    source = json.loads(
        INPUT_FILE.read_text(encoding="utf-8")
    )

    case = source["cases"]["PRE-01"]

    question = case["question"]
    answer = case["answer"]
    contexts = case["retrieved_contexts"]

    statements = extract_statements(answer)

    if not statements:
        print("No se encontraron afirmaciones numeradas.")
        return

    if not contexts:
        print("No existen contextos recuperados.")
        return

    print("=" * 55)
    print("LAIA - Evaluación de afirmaciones con Ragas")
    print("=" * 55)
    print("Caso: PRE-01")
    print("Afirmaciones encontradas:", len(statements))

    if OUTPUT_FILE.exists():
        report = json.loads(
            OUTPUT_FILE.read_text(encoding="utf-8")
        )

        # No reutilizar puntuaciones sobre otro contenido.
        previous = report.get("statements", [])
        same_input = (
            report.get("question") == question
            and report.get("answer") == answer
            and report.get("contexts") == contexts
            and report.get("judge_model") == JUDGE_MODEL
            and [
                item.get("text") for item in previous
            ] == [
                item["text"] for item in statements
            ]
        )

        if not same_input:
            raise RuntimeError(
                "El caso o el evaluador cambió. "
                "Usa otro archivo de resultados."
            )

    else:
        report = {
            "case_id": "PRE-01",
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "judge_model": JUDGE_MODEL,
            "evaluation_type": "statement_level",
            "statements": [
                {
                    **statement,
                    "faithfulness": None,
                    "error": None
                }
                for statement in statements
            ]
        }

        save_results(report)

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "No se encontró GROQ_API_KEY."
        )

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        max_retries=0,
        timeout=90.0
    )

    judge = llm_factory(
        JUDGE_MODEL,
        provider="openai",
        client=client,
        mode=Mode.MD_JSON,
        max_tokens=1200,
        reasoning_effort="low",
        temperature=0
    )

    metric = Faithfulness(llm=judge)

    for item in report["statements"]:
        number = item["number"]

        print(f"\nEvaluando afirmación {number}:")
        print(item["text"])

        if item["faithfulness"] is not None:
            print(
                "Resultado guardado:",
                item["faithfulness"]
            )
            continue

        try:
            score = await metric.ascore(
                user_input=question,
                response=item["text"],
                retrieved_contexts=contexts
            )

            item["faithfulness"] = float(score.value)
            item["error"] = None

            print(
                "Faithfulness:",
                item["faithfulness"]
            )

        except Exception as exc:
            item["error"] = (
                f"{type(exc).__name__}: {exc}"
            )

            print("Error:", item["error"])

            # Detenerse para evitar consumir cuota
            # cuando Groq o Instructor fallan.
            item["evaluated_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            save_results(report)
            break

        item["evaluated_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        save_results(report)

    print("\n" + "=" * 55)
    print("RESUMEN")
    print("=" * 55)

    completed = [
        item for item in report["statements"]
        if item["faithfulness"] is not None
    ]

    for item in report["statements"]:
        value = item["faithfulness"]

        if value is None:
            label = "Pendiente"
        else:
            label = f"{value:.4f}"

        print(
            f"Afirmación {item['number']}: {label}"
        )

    if completed:
        average = sum(
            item["faithfulness"] for item in completed
        ) / len(completed)

        print(
            "\nPromedio exploratorio "
            "de afirmaciones evaluadas:",
            round(average, 4)
        )

    print(
        "\nEvaluadas:",
        len(completed),
        "/",
        len(report["statements"])
    )

    print("\nResultados guardados en:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    asyncio.run(main())

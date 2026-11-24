
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from instructor import Mode

from dotenv import load_dotenv
from openai import AsyncOpenAI

from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness

from core.models.groq_provider import GroqProvider
from core.rag.rag_service import RAGService


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "evaluation" / "results"
OUTPUT_FILE = OUTPUT_DIR / "ragas_first_run.json"

GENERATOR_MODEL = "qwen/qwen3.8-27b"
JUDGE_MODEL = "openai/gpt-oss-20b"

CASES = [
    {
        "id": "PRE-01",
        "scope": "pregrado",
        "question": "¿Qué debo hacer para graduarme?"
    },
]


def save_report(report):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    temporary = OUTPUT_FILE.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    temporary.replace(OUTPUT_FILE)


async def evaluate_with_retries(
    metric, question, answer, contexts
):
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            return await metric.ascore(
                user_input=question,
                response=answer,
                retrieved_contexts=contexts
            )

        except Exception as exc:
            error_name = type(exc).__name__

            if error_name != "RateLimitError":
                raise

            message = str(exc)

            # Si una solicitud individual supera el
            # límite, esperar no solucionará el error.
            if "Request too large" in message:
                raise

            if attempt == max_attempts - 1:
                raise

            # Damos margen para recuperar la cuota.
            delay = 70

            print(
                f"Groq alcanzó su límite OTPM. "
                f"Reintento {attempt + 1}/2 "
                f"tras {delay} segundos."
            )

            await asyncio.sleep(delay)



async def main():
    load_dotenv(ROOT / ".env")

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("Falta GROQ_API_KEY.")

    provider = GroqProvider(model=GENERATOR_MODEL)
    rag = RAGService(provider=provider)

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        timeout=60.0,
        max_retries=0
    )

    judge = llm_factory(
    JUDGE_MODEL,
    provider="openai",
    client=client,
    mode=Mode.MD_JSON,
    max_tokens=768,
    temperature=0
)

    metric = Faithfulness(llm=judge)

    report = {
        "generator_model": GENERATOR_MODEL,
        "judge_model": JUDGE_MODEL,
        "metric": "faithfulness",
        "cases": {}
    }

    if OUTPUT_FILE.exists():
        report = json.loads(
            OUTPUT_FILE.read_text(encoding="utf-8")
        )

    report.setdefault("cases", {})

    report["generator_model"] = GENERATOR_MODEL
    report["judge_model"] = JUDGE_MODEL



    for case in CASES:
        case_id = case["id"]

        print(f"\nEvaluando: {case_id}")

        row = report["cases"].get(case_id, {})

        # Reutilizar respuestas ya generadas.
        if (
            row.get("answer")
            and row.get("retrieved_contexts")
        ):
            print("Usando respuesta guardada.")

        else:
            try:
                print("Generando respuesta...")

                result = rag.ask(
                    question=case["question"],
                    scope=case["scope"],
                    assistant_type="estudiante"
                )

                row = {
                    "id": case_id,
                    "scope": case["scope"],
                    "question": case["question"],
                    "answer": result["answer"],
                    "sources": result.get(
                        "sources", []
                    ),
                    "retrieved_contexts": result.get(
                        "retrieved_contexts", []
                    ),
                    "faithfulness": None,
                    "error": None
                }

                report["cases"][case_id] = row

                # Guardar ANTES de llamar a Ragas.
                save_report(report)
                print("Respuesta guardada.")

            except Exception as exc:
                print(
                    "Error de generación:",
                    type(exc).__name__,
                    str(exc)
                )

                # No interrumpir todo el experimento.
                continue

        if row.get("faithfulness") is not None:
            print(
                "Evaluación ya realizada:",
                row["faithfulness"]
            )
            continue

        if not row.get("retrieved_contexts"):
            row["error"] = "Sin contexto recuperado."
            save_report(report)
            continue

        try:
            print("Ejecutando Faithfulness...")

            score = await evaluate_with_retries(
                metric=metric,
                question=case["question"],
                answer=row["answer"],
                contexts=row["retrieved_contexts"]
            )

            row["faithfulness"] = score.value
            row["error"] = None

            print("Faithfulness:", score.value)

        except Exception as exc:
            row["error"] = (
                f"{type(exc).__name__}: {exc}"
            )

            print(
                "Error de Ragas:",
                row["error"]
            )

        finally:
            row["evaluated_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            save_report(report)

    print("\nResultados:", OUTPUT_FILE)


if __name__ == "__main__":
    asyncio.run(main())


import asyncio
import json
import os
from pathlib import Path
from instructor.exceptions import IncompleteOutputException
from dotenv import load_dotenv
from openai import AsyncOpenAI
from instructor import Mode

from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness


ROOT = Path(__file__).resolve().parents[1]

RESULT_FILE = (
    ROOT / "evaluation" / "results"
    / "ragas_first_run.json"
)


async def main():
    load_dotenv(ROOT / ".env")

    report = json.loads(
        RESULT_FILE.read_text(encoding="utf-8")
    )

    case = report["cases"]["PRE-01"]

    # Primera afirmación de la respuesta real,
    # extraída sin reescribirla.
    answer = case["answer"]

    statements = [
        line.strip()
        for line in answer.splitlines()
        if line.strip()
        and line.strip()[0:1].isdigit()
    ]

    if not statements:
        print("No se encontraron afirmaciones numeradas.")
        return

    partial_answer = statements[0]

    contexts = case["retrieved_contexts"]

    print("Afirmación evaluada:")
    print(partial_answer)

    client = AsyncOpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
        max_retries=0
    )

    judge = llm_factory(
    "openai/gpt-oss-20b",
    provider="openai",
    client=client,
    mode=Mode.MD_JSON,
    max_tokens=1200,
    reasoning_effort="low",
    temperature=0
)

    metric = Faithfulness(llm=judge)

    
    try:
        score = await metric.ascore(
            user_input=case["question"],
            response=partial_answer,
            retrieved_contexts=contexts
        )

        print("\nFaithfulness parcial:", score.value)

    except IncompleteOutputException as exc:
        print("\nSALIDA INCOMPLETA DEL EVALUADOR")

        completion = getattr(
            exc, "last_completion", None
        )

        if completion is not None:
            choices = getattr(
                completion, "choices", []
            )

            if choices:
                choice = choices[0]

                print(
                    "Motivo de finalización:",
                    choice.finish_reason
                )

                content = (
                    choice.message.content or ""
                )

                print(
                    "Longitud del contenido:",
                    len(content)
                )

                print(
                    "Últimos caracteres:",
                    repr(content[-300:])
                )

            usage = getattr(
                completion, "usage", None
            )

            if usage is not None:
                print("Consumo:", usage)

        else:
            print(
                "Instructor no proporcionó "
                "la última respuesta del modelo."
            )



if __name__ == "__main__":
    asyncio.run(main())

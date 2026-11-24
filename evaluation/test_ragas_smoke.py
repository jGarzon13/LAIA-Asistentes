
import asyncio
import os
import traceback

from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from instructor import Mode

from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness


ROOT = Path(__file__).resolve().parents[1]


async def main():
    load_dotenv(ROOT / ".env")

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
        max_tokens=768,
        temperature=0
    )

    metric = Faithfulness(llm=judge)

    print("Probando Ragas con un caso mínimo...")

    try:
        score = await metric.ascore(
            user_input="¿Cuál es la capital de Colombia?",
            response="La capital de Colombia es Bogotá.",
            retrieved_contexts=[
                "Bogotá es la capital de Colombia."
            ]
        )

        print("Faithfulness:", score.value)

    except Exception as exc:
        print("Tipo de error:", type(exc).__name__)
        print("Descripción:", str(exc))
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())


"""Primera ejecución registrada de GraphRAG + Groq."""

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from core.rag.graph.graph_rag_service import GraphRAGService


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT / "evaluation/results/graph_first_run.json"
QUESTION = "¿Qué debo hacer para graduarme de pregrado?"
CASE_ID = "PRE-01"

load_dotenv(ROOT / ".env")

MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")


def write_json_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")

    try:
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()


def generate_with_groq(prompt):
    key = os.getenv("GROQ_API_KEY")

    if not key:
        raise RuntimeError("Falta GROQ_API_KEY en .env")

    client = OpenAI(
        api_key=key,
        base_url="https://api.groq.com/openai/v1",
        max_retries=0,
        timeout=90,
        default_headers={
            "User-Agent": "LAIA-GraphRAG/0.1"
        },
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=900,
    )

    answer = response.choices[0].message.content

    if not answer or not answer.strip():
        raise RuntimeError("Groq devolvió una respuesta vacía.")

    return answer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Reemplazar una ejecución guardada",
    )
    args = parser.parse_args()

    if OUTPUT_FILE.exists() and not args.overwrite:
        print(f"Ya existe: {OUTPUT_FILE}")
        print("No se repetirá la llamada a Groq.")
        return

    service = GraphRAGService()
    prepared = service.prepare(QUESTION, scope="pregrado")

    if prepared["status"] != "ok":
        raise RuntimeError(
            f"Recuperación incompleta: {prepared['status']}"
        )

    contexts = prepared["retrieved_contexts"]

    if not contexts:
        raise RuntimeError("No se recuperó evidencia.")

    print("Caso:", CASE_ID)
    print("Modelo:", MODEL)
    print("Contextos:", len(contexts))
    print("Consultando Groq...")

    # Una sola llamada al modelo generador.
    answer = generate_with_groq(prepared["prompt"])

    evidence_hash = hashlib.sha256(
        json.dumps(
            contexts,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()

    data = {
        "experiment": "graph_rag_manual_v1",
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "model": MODEL,
        "retrieval_strategy": (
            "manual_academic_graph_with_evidence_expansion"
        ),
        "evidence_sha256": evidence_hash,
        "cases": {
            CASE_ID: {
                "question": QUESTION,
                "scope": "pregrado",
                "answer": answer,
                "retrieved_contexts": contexts,
                "sources": prepared["sources"],
                "facts": prepared["facts"],
            }
        },
    }

    write_json_atomic(OUTPUT_FILE, data)

    print("\nRESPUESTA:\n")
    print(answer)
    print("\nResultado guardado en:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()

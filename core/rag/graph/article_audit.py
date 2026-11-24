
"""Auditoría de candidatos a artículos para GraphRAG."""

import json
from pathlib import Path

from core.rag.graph.article_detector import (
    detect_article_headings,
)


ROOT = Path(__file__).resolve().parents[3]
INDEX_FILE = ROOT / "knowledge/index/chunks.json"

TARGETS = [
    "Reglamento-posgrados-Res-CA-6605.pdf",
    "Res-CA-6603.pdf",
    "Res_CS_226.pdf",
    "res-ca-6865-requisitos-titulo-programas-pregrado-profesional.pdf",
]


def audit_articles(chunks, targets=TARGETS, limit=15):
    for filename in targets:
        document_chunks = [
            chunk for chunk in chunks
            if chunk.get("filename") == filename
        ]

        print("\n" + "=" * 75)
        print("DOCUMENTO:", filename)
        print("FRAGMENTOS:", len(document_chunks))

        candidates = []

        for chunk in document_chunks:
            matches = detect_article_headings(
                chunk.get("text", "")
            )

            for match in matches:
                position = match["position"]
                text = chunk["text"]

                start = max(0, position - 55)
                end = min(len(text), position + 110)

                context = text[start:end].replace(
                    "\n", " "
                )

                candidates.append({
                    "article": match["number"],
                    "page": chunk["page"],
                    "chunk_id": chunk["id"],
                    "requires_review": chunk.get(
                        "requires_review", False
                    ),
                    "context": context,
                })

        print("CANDIDATOS:", len(candidates))

        suspicious = [
            item for item in candidates
            if item["article"] >= 90
        ]

        print(
            "CANDIDATOS >= 90:",
            len(suspicious),
        )

        print("\nPRIMEROS CANDIDATOS:")

        for item in candidates[:limit]:
            print(
                f"\nArtículo candidato: {item['article']}"
                f" | Página: {item['page']}"
                f" | Revisar: {item['requires_review']}"
            )
            print("Fragmento:", item["chunk_id"])
            print("Contexto:", item["context"])

        if suspicious:
            print("\nEJEMPLOS DE NÚMEROS ALTOS:")

            for item in suspicious[:8]:
                print(
                    f"\nArtículo {item['article']}"
                    f" | Página {item['page']}"
                )
                print(item["context"])


def main():
    data = json.loads(
        INDEX_FILE.read_text(encoding="utf-8")
    )

    audit_articles(data["chunks"])


if __name__ == "__main__":
    main()


"""Detección experimental de encabezados de artículos."""

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INDEX_FILE = ROOT / "knowledge/index/chunks.json"

EXCLUDED = {"procedimiento_academico_ficticio.txt"}


def normalize(text):
    text = unicodedata.normalize("NFD", text)
    return "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )


# Exige ARTÍCULO en mayúsculas y número,
# para reducir confusiones con referencias en prosa.
ARTICLE_PATTERN = re.compile(
    r"\bARTICULO\s+(?:N[Oº°]\.?\s*)?"
    r"(\d{1,3})\s*[º°.]?",
)


def detect_article_headings(text):
    """Detecta candidatos; no garantiza que sean encabezados."""

    normalized = normalize(text)
    return [
        {
            "number": int(match.group(1)),
            "position": match.start(),
        }
        for match in ARTICLE_PATTERN.finditer(normalized)
    ]


def scan_corpus(chunks):
    results = defaultdict(list)

    for chunk in chunks:
        filename = chunk["filename"]

        if filename.casefold() in EXCLUDED:
            continue

        matches = detect_article_headings(chunk["text"])

        for match in matches:
            results[filename].append({
                "article": match["number"],
                "chunk_id": chunk["id"],
                "page": chunk["page"],
                "requires_review": chunk.get(
                    "requires_review", False
                ),
            })

    return dict(results)


def main():
    data = json.loads(
        INDEX_FILE.read_text(encoding="utf-8")
    )

    findings = scan_corpus(data["chunks"])

    print("LAIA - Diagnóstico de artículos")
    print("=" * 65)

    for filename in sorted(findings):
        articles = findings[filename]
        unique = sorted({
            item["article"] for item in articles
        })

        print(f"\n{filename}")
        print("Candidatos:", len(articles))
        print("Números distintos:", len(unique))
        print("Primeros números:", unique[:20])

        flagged = sum(
            bool(item["requires_review"])
            for item in articles
        )

        print("Candidatos en fragmentos para revisar:", flagged)

    print("\nRESUMEN")
    print("Documentos con candidatos:", len(findings))
    print(
        "Encabezados candidatos:",
        sum(len(items) for items in findings.values())
    )


if __name__ == "__main__":
    main()

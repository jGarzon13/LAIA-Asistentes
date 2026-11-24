
"""Clasificación conservadora de artículos y referencias de LAIA."""

import json
import re
from collections import Counter
from pathlib import Path

from core.rag.graph.article_detector import (
    detect_article_headings,
)

ROOT = Path(__file__).resolve().parents[3]
CHUNKS_FILE = ROOT / "knowledge/index/chunks.json"
ARTICLES_FILE = ROOT / "knowledge/graph/article_index.json"
OUTPUT_FILE = ROOT / "knowledge/graph/classified_articles.json"

REFERENCE_PATTERN = re.compile(
    r"(?:\bmodifica(?:r|do|da)?\b|"
    r"\bderoga(?:r|do|da)?\b|"
    r"\bseg[uú]n\b|"
    r"\bconforme\s+(?:a|al)\b|"
    r"\bde\s+acuerdo\s+con\b|"
    r"\bprevisto\s+en\b|"
    r"\bestablecido\s+en\b|"
    r"\bliteral\b|"
    r"\bnumeral\b)"
    r"[\s\S]{0,55}$",
    re.IGNORECASE,
)

HEADING_PATTERN = re.compile(
    r"^\s*(?:[º°o.]|:|-)*\s*:?\s*"
    r"(?:[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s,/-]{2,70}"
    r"|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,})"
)


def classify_occurrence(
    text,
    position,
    detected_number,
    proposed_numbers=None,
    requires_review=False,
):
    """Clasifica una aparición sin confirmar su validez normativa."""

    proposed_numbers = proposed_numbers or []

    matches = detect_article_headings(text)

    match = next(
        (
            m for m in matches
            if m["position"] == position
            and m["number"] == detected_number
        ),
        None,
    )

    if match is None:
        return {
            "classification": "ambiguous",
            "reason": "No se pudo reconstruir la coincidencia",
        }

    before = text[max(0, position - 100):position]

    # Extraer el texto que sigue al número.
    raw_match = re.search(
    r"\bART[ÍI]CULO\s+(?:N[Oº°]\.?\s*)?"
    + str(detected_number) + r"(?!\d)",
    text[position:],
)

    if raw_match is None:
        return {
            "classification": "ambiguous",
            "reason": "Encabezado no localizable en el texto original",
        }

    after = text[
        position + raw_match.end():
        position + raw_match.end() + 100
    ]

    if REFERENCE_PATTERN.search(before):
        return {
            "classification": "reference_candidate",
            "reason": "Contexto compatible con referencia normativa",
        }

    if proposed_numbers:
        return {
            "classification": "ocr_suspected",
            "reason": (
                "Numeración con propuesta OCR no verificada"
            ),
        }

    if HEADING_PATTERN.match(after):
        return {
            "classification": "heading_candidate",
            "reason": (
                "Formato compatible con encabezado; "
                "pendiente de validación documental"
            ),
        }

    return {
        "classification": "ambiguous",
        "reason": (
            "Contexto insuficiente para distinguir "
            "encabezado y referencia"
        ),
    }


def classify_index(article_documents, chunks):
    chunks_by_id = {
        chunk["id"]: chunk for chunk in chunks
    }

    output = []

    for document in article_documents:
        classified = []

        for candidate in document["candidates"]:
            occurrences = []

            for evidence in candidate["evidence"]:
                chunk = chunks_by_id.get(
                    evidence["chunk_id"]
                )

                if chunk is None:
                    result = {
                        "classification": "ambiguous",
                        "reason": "Fragmento no encontrado",
                    }
                else:
                    result = classify_occurrence(
                        text=chunk["text"],
                        position=evidence["position"],
                        detected_number=(
                            candidate["detected_number"]
                        ),
                        proposed_numbers=(
                            candidate["proposed_numbers"]
                        ),
                        requires_review=(
                            evidence["requires_review"]
                        ),
                    )

                occurrences.append({
                    **evidence,
                    **result,
                })

            classified.append({
                "detected_number": (
                    candidate["detected_number"]
                ),
                "proposed_numbers": (
                    candidate["proposed_numbers"]
                ),
                "status": candidate["status"],
                "occurrences": occurrences,
            })

        output.append({
            "document_id": document["document_id"],
            "filename": document["filename"],
            "articles": classified,
        })

    return output


def main():
    source = json.loads(
        CHUNKS_FILE.read_text(encoding="utf-8")
    )
    article_source = json.loads(
        ARTICLES_FILE.read_text(encoding="utf-8")
    )

    documents = classify_index(
        article_source["documents"],
        source["chunks"],
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True, exist_ok=True
    )

    payload = {
        "schema_version": 1,
        "type": "article_occurrence_classification",
        "documents": documents,
    }

    temp = OUTPUT_FILE.with_suffix(".json.tmp")

    try:
        temp.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temp.replace(OUTPUT_FILE)
    finally:
        if temp.exists():
            temp.unlink()

    counts = Counter(
        occurrence["classification"]
        for doc in documents
        for article in doc["articles"]
        for occurrence in article["occurrences"]
    )

    print("\nLAIA - Clasificación de artículos")
    print("Documentos:", len(documents))

    print("\nCLASIFICACIONES:")
    for name, count in sorted(counts.items()):
        print(f"- {name}: {count}")

    print("\nTotal apariciones:", sum(counts.values()))
    print("Archivo:", OUTPUT_FILE)


if __name__ == "__main__":
    main()

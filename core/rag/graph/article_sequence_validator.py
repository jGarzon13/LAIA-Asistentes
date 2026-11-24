
"""Auditoría de secuencias de artículos de LAIA.

No modifica números ni valida correcciones automáticamente.
"""

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INPUT_FILE = ROOT / "knowledge/graph/article_index.json"
OUTPUT_FILE = ROOT / "knowledge/graph/article_sequences.csv"


def chunk_order(chunk_id):
    match = re.search(r"-C(\d+)$", chunk_id)
    return int(match.group(1)) if match else 10**9


def ordered_candidates(document):
    rows = []

    for candidate in document["candidates"]:
        for evidence in candidate["evidence"]:
            rows.append({
                "document": document["filename"],
                "detected": candidate["detected_number"],
                "proposed": ",".join(
                    map(str, candidate["proposed_numbers"])
                ),
                "status": candidate["status"],
                "page": evidence["page"],
                "chunk_id": evidence["chunk_id"],
                "position": evidence["position"],
                "chunk_order": chunk_order(
                    evidence["chunk_id"]
                ),
            })

    rows.sort(
        key=lambda r: (r["chunk_order"], r["position"])
    )

    # Conserva la primera aparición de cada candidato
    # numérico; las otras quedan en article_index.json.
    unique = []
    seen = set()

    for row in rows:
        if row["detected"] in seen:
            continue

        seen.add(row["detected"])
        unique.append(row)

    return unique


def build_report(documents):
    report = []

    for document in documents:
        ordered = ordered_candidates(document)

        for i, row in enumerate(ordered):
            previous = (
                ordered[i - 1]["detected"]
                if i > 0 else None
            )
            following = (
                ordered[i + 1]["detected"]
                if i + 1 < len(ordered) else None
            )

            report.append({
                "document": row["document"],
                "page": row["page"],
                "detected": row["detected"],
                "proposed": row["proposed"],
                "previous_detected": previous,
                "next_detected": following,
                "status": row["status"],
                "chunk_id": row["chunk_id"],
            })

    return report


def main():
    data = json.loads(
        INPUT_FILE.read_text(encoding="utf-8")
    )

    report = build_report(data["documents"])

    OUTPUT_FILE.parent.mkdir(
        parents=True, exist_ok=True
    )

    fields = [
        "document", "page", "detected", "proposed",
        "previous_detected", "next_detected",
        "status", "chunk_id",
    ]

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=fields
        )
        writer.writeheader()
        writer.writerows(report)

    print("Candidatos analizados:", len(report))
    print("Reporte:", OUTPUT_FILE)


if __name__ == "__main__":
    main()

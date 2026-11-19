
import json
from datetime import datetime, timezone
from pathlib import Path

from core.rag.document_loader import (
    SUPPORTED_EXTENSIONS,
    load_document
)
from core.rag.chunker import chunk_document


ROOT = Path(__file__).resolve().parents[2]

DOCUMENTS_DIR = ROOT / "knowledge" / "documents"
INDEX_FILE = ROOT / "knowledge" / "index" / "chunks.json"


def build_index(
    documents_dir: Path = DOCUMENTS_DIR,
    index_file: Path = INDEX_FILE
) -> dict:

    documents_dir = Path(documents_dir)
    index_file = Path(index_file)

    documents_dir.mkdir(parents=True, exist_ok=True)
    index_file.parent.mkdir(parents=True, exist_ok=True)

    documents = []
    chunks = []
    errors = []

    files = sorted(
        path
        for path in documents_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    for path in files:
        try:
            document = load_document(path)

            if not document["sections"]:
                errors.append({
                    "file": path.name,
                    "error": "No se extrajo texto."
                })
                continue

            document_chunks = chunk_document(document)

            documents.append({
                "id": document["id"],
                "filename": document["filename"],
                "format": document["format"],
                "chunk_count": len(document_chunks)
            })

            chunks.extend(document_chunks)

        except Exception as exc:
            errors.append({
                "file": path.name,
                "error": f"{type(exc).__name__}: {exc}"
            })

    index = {
        "version": "0.1.0",
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "documents": documents,
        "chunks": chunks,
        "errors": errors
    }

    index_file.write_text(
        json.dumps(
            index,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return index


def main():
    print("=" * 50)
    print("LAIA - Construcción del índice documental")
    print("=" * 50)

    index = build_index()

    print(f"Documentos: {len(index['documents'])}")
    print(f"Fragmentos: {len(index['chunks'])}")
    print(f"Incidencias: {len(index['errors'])}")

    for error in index["errors"]:
        print(f"Advertencia: {error['file']}: {error['error']}")

    print(f"\nÍndice: {INDEX_FILE}")


if __name__ == "__main__":
    main()

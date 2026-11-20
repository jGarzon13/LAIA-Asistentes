
import hashlib
import json
import os
import tempfile
from core.rag.academic_metadata import sync_metadata

from collections import Counter, defaultdict
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

INDEX_VERSION = "0.2.0"


def calculate_hash(path: Path) -> str:
    """Calcula SHA-256 sin cargar todo el archivo en RAM."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            digest.update(block)

    return digest.hexdigest()


def load_previous_index(index_file: Path) -> dict:
    """Carga el índice existente, si lo hay."""

    if not index_file.is_file():
        return {"documents": [], "chunks": []}

    return json.loads(
        index_file.read_text(encoding="utf-8")
    )


def save_index_atomic(index: dict, index_file: Path):
    """Escribe un archivo temporal antes de sustituir el índice."""

    index_file.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=index_file.parent,
            suffix=".tmp",
            delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)

            json.dump(
                index,
                temporary,
                ensure_ascii=False,
                indent=2
            )

        os.replace(temporary_path, index_file)

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()


def build_index(
    documents_dir: Path = DOCUMENTS_DIR,
    index_file: Path = INDEX_FILE
) -> dict:
    """Indexa únicamente documentos nuevos o modificados."""

    documents_dir = Path(documents_dir)
    index_file = Path(index_file)

    documents_dir.mkdir(parents=True, exist_ok=True)
    index_file.parent.mkdir(parents=True, exist_ok=True)

    previous = load_previous_index(index_file)

    previous_documents = previous.get("documents", [])
    previous_chunks = previous.get("chunks", [])

    # Índices para localizar documentos ya procesados.
    previous_by_path = {}
    previous_by_filename = defaultdict(list)

    for document in previous_documents:
        source_path = document.get("source_path")

        if source_path:
            previous_by_path[source_path] = document

        previous_by_filename[
            document["filename"]
        ].append(document)

    # Los fragmentos antiguos se agrupan por ID y nombre.
    chunks_by_document = defaultdict(list)

    for chunk in previous_chunks:
        key = (
            chunk.get("document_id"),
            chunk.get("filename")
        )
        chunks_by_document[key].append(chunk)

    files = sorted(
        (
            path for path in documents_dir.rglob("*")
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ),
        key=lambda path: str(path).lower()
    )

    filename_counts = Counter(
        path.name for path in files
    )

    documents = []
    chunks = []
    errors = []

    stats = {
        "new": 0,
        "modified": 0,
        "reused": 0,
        "removed": 0,
        "failed": 0
    }

    active_paths = {
        path.relative_to(documents_dir).as_posix()
        for path in files
    }

    # Contabilizar documentos que ya no existen.
    for old_document in previous_documents:
        old_path = old_document.get("source_path")

        if old_path:
            if old_path not in active_paths:
                stats["removed"] += 1
        elif filename_counts[old_document["filename"]] == 0:
            stats["removed"] += 1

    total_files = len(files)

    print("\nLAIA - Indexación incremental")
    print("=" * 55)

    for position, path in enumerate(files, start=1):
        relative_path = path.relative_to(
            documents_dir
        ).as_posix()

        print(
            f"\n[{position}/{total_files}] {relative_path}",
            flush=True
        )

        old_document = previous_by_path.get(
            relative_path
        )

       
        if old_document is None:
            matches = previous_by_filename.get(
                path.name, []
            )

            if (
                filename_counts[path.name] == 1
                and len(matches) == 1
                and not matches[0].get("source_path")
            ):
                old_document = matches[0]

        try:
            file_hash = calculate_hash(path)
            document_id = file_hash[:16]

            old_chunks = []

            if old_document:
                old_key = (
                    old_document["id"],
                    old_document["filename"]
                )

                old_chunks = chunks_by_document.get(
                    old_key, []
                )

            unchanged = (
                old_document is not None
                and old_document["id"] == document_id
                and old_document.get(
                    "sha256", file_hash
                ) == file_hash
                and bool(old_chunks)
            )

            if unchanged:
                # Reutilizar fragmentos existentes.
                document_record = {
                    **old_document,
                    "source_path": relative_path,
                    "sha256": file_hash
                }

                documents.append(document_record)
                chunks.extend(old_chunks)

                stats["reused"] += 1

                print(
                    f"  REUTILIZADO: {len(old_chunks)} fragmentos",
                    flush=True
                )
                continue

            # Documento nuevo o con contenido modificado.
            document = load_document(path)

            if not document["sections"]:
                raise ValueError(
                    "No se pudo extraer contenido del documento."
                )

            document_chunks = chunk_document(document)

            if not document_chunks:
                raise ValueError(
                    "No se generaron fragmentos."
                )

            documents.append({
                "id": document["id"],
                "sha256": file_hash,
                "source_path": relative_path,
                "filename": document["filename"],
                "format": document["format"],
                "chunk_count": len(document_chunks)
            })

            chunks.extend(document_chunks)

            if old_document:
                stats["modified"] += 1
                action = "ACTUALIZADO"
            else:
                stats["new"] += 1
                action = "NUEVO"

            print(
                f"  {action}: "
                f"{len(document_chunks)} fragmentos",
                flush=True
            )

        except Exception as exc:
            stats["failed"] += 1

            errors.append({
                "file": relative_path,
                "error": f"{type(exc).__name__}: {exc}"
            })

            print(
                f"  ERROR: {type(exc).__name__}: {exc}",
                flush=True
            )

    index = {
        "version": INDEX_VERSION,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "documents": documents,
        "chunks": chunks,
        "errors": errors,
        "stats": stats
    }

    
    save_index_atomic(index, index_file)

    # El catálogo se guarda junto al espacio
    # documental, fuera de la carpeta index.
    metadata_file = (
        index_file.parent.parent / "metadata.json"
    )

    catalog = sync_metadata(
        index=index,
        metadata_file=metadata_file
    )

    index["metadata_stats"] = catalog["stats"]

    return index



def main():
    index = build_index()
    stats = index["stats"]

    print("\n" + "=" * 55)
    print("LAIA - Resumen de indexación")
    print("=" * 55)

    print(f"Documentos: {len(index['documents'])}")
    print(f"Fragmentos: {len(index['chunks'])}")
    print(f"Nuevos: {stats['new']}")
    print(f"Modificados: {stats['modified']}")
    print(f"Reutilizados: {stats['reused']}")
    print(f"Eliminados: {stats['removed']}")
    print(f"Fallidos: {stats['failed']}")
    print(f"Incidencias: {len(index['errors'])}")

    print(f"\nÍndice: {INDEX_FILE}")


    metadata_stats = index["metadata_stats"]

    print("\nClasificación documental:")
    print(f"  Nuevos: {metadata_stats['created']}")
    print(f"  Conservados: {metadata_stats['preserved']}")
    print(f"  Versiones modificadas: {metadata_stats['changed']}")
    print(f"  Retirados: {metadata_stats['removed']}")



if __name__ == "__main__":
    main()


import json
import os
import re
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
METADATA_FILE = ROOT / "knowledge" / "metadata.json"

EDITABLE_FIELDS = {
    "scope",
    "document_type",
    "modality",
    "version_date",
    "validity",
}

ALLOWED_VALUES = {
    "scope": {
        "pregrado", "posgrado", "general",
        "sin_clasificar"
    },
    "document_type": {
        "reglamento", "modificacion",
        "resolucion", "politica", "codigo",
        "procedimiento", "otro"
    },
    "modality": {
        "virtual", "presencial", "general",
        "sin_clasificar"
    },
    "validity": {
        "no_verificada", "vigente",
        "reemplazada", "historica"
    },
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )
    return re.sub(r"[_\-.]+", " ", value.lower())


def infer_metadata(filename: str) -> dict:
    """Clasificación conservadora a partir del nombre."""

    name = normalize(Path(filename).stem)

    if re.search(r"\bposgrados?\b|\bpostgrados?\b", name):
        scope = "posgrado"
    elif re.search(r"\bpregrados?\b", name):
        scope = "pregrado"
    elif any(term in name for term in (
        "codigo de etica",
        "proteccion datos",
        "proyeccion social"
    )):
        scope = "general"
    else:
        scope = "sin_clasificar"

    if "modifica" in name:
        document_type = "modificacion"
    elif "reglamento" in name:
        document_type = "reglamento"
    elif "politica" in name:
        document_type = "politica"
    elif "codigo" in name:
        document_type = "codigo"
    elif "procedimiento" in name:
        document_type = "procedimiento"
    elif re.search(r"\bres\b|\bresolucion\b", name):
        document_type = "resolucion"
    else:
        document_type = "otro"

    if re.search(r"\bvirtual\b", name):
        modality = "virtual"
    elif re.search(r"\bpresencial\b", name):
        modality = "presencial"
    else:
        modality = "sin_clasificar"

    # Reconocer solamente fechas ISO explícitas.
    # No inferir fecha normativa a partir de un
    # número aislado en el nombre.
    match = re.search(
        r"\b(20\d{2})[ -](0[1-9]|1[0-2])"
        r"[ -](0[1-9]|[12]\d|3[01])\b",
        name
    )

    version_date = None

    if match:
        candidate = "-".join(match.groups())
        try:
            from datetime import date
            version_date = date.fromisoformat(
                candidate
            ).isoformat()
        except ValueError:
            pass

    return {
        "scope": scope,
        "document_type": document_type,
        "modality": modality,
        "version_date": version_date,
        "validity": "no_verificada"
    }


def validate_overrides(overrides: dict) -> dict:
    """Acepta únicamente correcciones conocidas y válidas."""

    if not isinstance(overrides, dict):
        return {}

    valid = {}

    for field, value in overrides.items():
        if field not in EDITABLE_FIELDS:
            continue

        if field == "version_date":
            if value is None:
                valid[field] = None
            elif isinstance(value, str):
                try:
                    from datetime import date
                    valid[field] = date.fromisoformat(
                        value
                    ).isoformat()
                except ValueError:
                    pass
            continue

        if (
            isinstance(value, str)
            and value in ALLOWED_VALUES[field]
        ):
            valid[field] = value

    return valid


def save_json_atomic(data: dict, destination: Path):
    destination.parent.mkdir(
        parents=True, exist_ok=True
    )

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            suffix=".tmp",
            delete=False
        ) as file:
            temporary_path = Path(file.name)
            json.dump(
                data, file, ensure_ascii=False, indent=2
            )

        os.replace(temporary_path, destination)

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()


def sync_metadata(
    index: dict,
    metadata_file: str | Path = METADATA_FILE
) -> dict:
    """Sincroniza metadatos sin rehacer extracción ni OCR."""

    metadata_file = Path(metadata_file)

    previous = {}

    if metadata_file.exists():
        data = json.loads(
            metadata_file.read_text(encoding="utf-8")
        )
        previous = data.get("documents", {})

        if not isinstance(previous, dict):
            raise ValueError(
                "Catálogo anterior inválido."
            )

    previous_by_path = {
        record.get("source_path"): record
        for record in previous.values()
        if isinstance(record, dict)
        and record.get("source_path")
    }

    documents = {}
    stats = {
        "created": 0,
        "preserved": 0,
        "changed": 0,
        "removed": 0
    }

    for document in index.get("documents", []):
        document_id = document["id"]
        filename = document["filename"]
        source_path = document.get(
            "source_path", filename
        )

        content_hash = document.get(
            "sha256", document_id
        )

        old = previous_by_path.get(source_path)

        # Solo preservar correcciones cuando el
        # contenido sigue siendo exactamente el mismo.
        same_content = (
            old is not None
            and old.get("sha256") == content_hash
            and old.get("filename") == filename
        )

        inferred = infer_metadata(filename)

        if same_content:
            overrides = validate_overrides(
                old.get("manual_overrides", {})
            )
            review_status = old.get(
                "review_status", "pendiente"
            )
            if review_status not in {
                "pendiente", "revisada"
            }:
                review_status = "pendiente"

            stats["preserved"] += 1
        else:
            overrides = {}
            review_status = "pendiente"

            if old is None:
                stats["created"] += 1
            else:
                stats["changed"] += 1

        documents[source_path] = {
            "document_id": document_id,
            "sha256": content_hash,
            "filename": filename,
            "source_path": source_path,
            "inferred": inferred,
            "manual_overrides": overrides,
            "effective": {
                **inferred,
                **overrides
            },
            "review_status": review_status
        }

    stats["removed"] = len(
        set(previous) - set(documents)
    )

    catalog = {
        "version": "0.1.0",
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "documents": documents,
        "stats": stats
    }

    save_json_atomic(catalog, metadata_file)

    return catalog

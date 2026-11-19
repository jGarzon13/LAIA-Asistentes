
import hashlib
from pathlib import Path

from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def load_document(file_path: str | Path) -> dict:
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"No existe: {path}")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Formato no soportado: {extension}")

    # Identificador estable basado en el contenido.
    document_id = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()[:16]

    sections = []

    if extension == ".pdf":
        reader = PdfReader(str(path))

        for page_number, page in enumerate(
            reader.pages, start=1
        ):
            text = page.extract_text() or ""

            if text.strip():
                sections.append({
                    "page": page_number,
                    "text": text.strip()
                })

    elif extension == ".docx":
        document = Document(str(path))

        parts = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        for table in document.tables:
            for row in table.rows:
                values = [
                    cell.text.strip()
                    for cell in row.cells
                ]
                if any(values):
                    parts.append(" | ".join(values))

        if parts:
            sections.append({
                "page": None,
                "text": "\n".join(parts)
            })

    else:
        text = path.read_text(encoding="utf-8-sig")

        if text.strip():
            sections.append({
                "page": None,
                "text": text.strip()
            })

    return {
        "id": document_id,
        "filename": path.name,
        "format": extension,
        "sections": sections
    }

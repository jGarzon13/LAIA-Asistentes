
import hashlib
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from core.rag.ocr_processor import extract_scanned_page

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

        # Se abre con PyMuPDF solo si alguna
        # página necesita reconocimiento OCR.
        ocr_document = None

        try:
            for page_number, page in enumerate(
                reader.pages, start=1
            ):
                text = (page.extract_text() or "").strip()
                extraction_method = "text"

                # Si no hay texto extraíble, aplicar OCR.
                if not text:
                    if ocr_document is None:
                        import pymupdf
                        ocr_document = pymupdf.open(str(path))

                    scanned_page = ocr_document[page_number - 1]

                    text = extract_scanned_page(
                        scanned_page,
                        language="spa"
                    )

                    extraction_method = "ocr"

                if text.strip():
                    sections.append({
                        "page": page_number,
                        "text": text.strip(),
                        "extraction_method": extraction_method,
                        "requires_review": (
                            extraction_method == "ocr"
                        )
                    })

        finally:
            if ocr_document is not None:
                ocr_document.close()


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
                "text": "\n".join(parts),
                "extraction_method": "text",
                "requires_review": False
            })

    else:
        text = path.read_text(encoding="utf-8-sig")

        if text.strip():
            sections.append({
                "page": None,
                "text": text.strip(),
                "extraction_method": "text",
                "requires_review": False
            })

    return {
        "id": document_id,
        "filename": path.name,
        "format": extension,
        "sections": sections
    }

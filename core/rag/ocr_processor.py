
from io import BytesIO
from pathlib import Path
import shutil

import pymupdf
import pytesseract
from PIL import Image


def configure_tesseract():
    """Configura Tesseract en Windows si no está en PATH."""

    if shutil.which("tesseract"):
        return

    windows_path = Path(
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    if windows_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(
            windows_path
        )
    else:
        raise RuntimeError(
            "Tesseract OCR no está disponible."
        )


def extract_scanned_page(
    page: pymupdf.Page,
    language: str = "spa",
    dpi: int = 200
) -> str:
    """Extrae texto de una página PDF mediante OCR."""

    configure_tesseract()

    # Convierte la página en una imagen.
    pixmap = page.get_pixmap(
        dpi=dpi,
        colorspace=pymupdf.csRGB,
        alpha=False
    )

    image = Image.open(
        BytesIO(pixmap.tobytes("png"))
    )

    # Reconoce el texto en el idioma seleccionado.
    text = pytesseract.image_to_string(
        image,
        lang=language
    )

    return text.strip()

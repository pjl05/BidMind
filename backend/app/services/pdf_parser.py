import os
from typing import Optional
import hashlib

try:
    import pypdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from app.core.config import get_settings

settings = get_settings()


class PDFParser:
    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    def extract_text(self, file_path: str) -> str:
        """Extract text content from PDF file."""
        if not PDF_AVAILABLE:
            raise ImportError("pypdf is not installed")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            raise ValueError(f"PDF file too large: {file_size} bytes")

        text_parts = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_parts.append(f"[Page {i+1}]\n{text}")

        return "\n\n".join(text_parts)

    def get_page_count(self, file_path: str) -> int:
        """Get number of pages in PDF."""
        if not PDF_AVAILABLE:
            raise ImportError("pypdf is not installed")

        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            return len(reader.pages)


pdf_parser = PDFParser()
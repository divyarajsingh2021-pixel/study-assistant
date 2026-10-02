import os
from pathlib import Path
from typing import Any

import pypdf


class PDFService:
    @staticmethod
    def extract_text_and_pages(pdf_path: Path) -> list[dict[str, Any]]:
        """
        Extracts text from a PDF file page-by-page.
        Returns a list of dicts: [{"page": 1, "text": "..."}]
        """
        pages_content = []
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            for index, page in enumerate(reader.pages):
                raw_text = page.extract_text() or ""
                # Clean up excessive line breaks and whitespace
                cleaned_text = "\n".join(
                    line.strip() for line in raw_text.splitlines() if line.strip()
                )
                if cleaned_text:
                    pages_content.append({"page": index + 1, "text": cleaned_text})
        except Exception as e:
            raise RuntimeError(f"Error parsing PDF file: {str(e)}")

        return pages_content

    @staticmethod
    def get_document_meta(pdf_path: Path) -> dict[str, Any]:
        """
        Returns basic file metadata: page count, size in bytes.
        """
        file_size = os.path.getsize(pdf_path)
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            page_count = len(reader.pages)
        except Exception:
            page_count = 1

        return {"file_size": file_size, "page_count": page_count}


pdf_service = PDFService()

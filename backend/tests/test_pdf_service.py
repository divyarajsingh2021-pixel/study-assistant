from pathlib import Path

import pypdf
import pytest
from app.services.pdf_service import pdf_service


def test_get_document_meta_valid_pdf(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    with open(pdf_path, "wb") as f:
        writer.write(f)

    meta = pdf_service.get_document_meta(pdf_path)
    assert meta["page_count"] == 2
    assert meta["file_size"] > 0


def test_extract_text_and_pages_corrupted_file(tmp_path):
    corrupted_path = tmp_path / "corrupt.pdf"
    corrupted_path.write_bytes(b"not a valid pdf content")

    with pytest.raises(RuntimeError) as exc_info:
        pdf_service.extract_text_and_pages(corrupted_path)
    assert "Error parsing PDF" in str(exc_info.value)


def test_extract_text_from_sample_doc():
    sample_pdf = (
        Path(__file__).resolve().parent.parent / "sample_docs" / "Operating_Systems_Concurrency.pdf"
    )
    if sample_pdf.exists():
        pages = pdf_service.extract_text_and_pages(sample_pdf)
        assert len(pages) > 0
        assert pages[0]["page"] == 1
        assert len(pages[0]["text"]) > 20

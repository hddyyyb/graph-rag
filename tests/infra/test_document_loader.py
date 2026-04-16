from __future__ import annotations

from pathlib import Path

import pytest

from graph_rag.infra.document_loaders.simple_document_loader import SimpleDocumentLoader


def test_load_txt_success(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello\nworld", encoding="utf-8")

    loader = SimpleDocumentLoader()
    content = loader.load_from_path(str(file_path))

    assert content == "hello\nworld"


def test_load_unsupported_file_type_raises_error(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.md"
    file_path.write_text("# title", encoding="utf-8")

    loader = SimpleDocumentLoader()

    with pytest.raises(ValueError, match="unsupported file type"):
        loader.load_from_path(str(file_path))


def test_load_docx_success(tmp_path: Path) -> None:
    docx = pytest.importorskip("docx")

    file_path = tmp_path / "sample.docx"

    doc = docx.Document()
    doc.add_paragraph("first paragraph")
    doc.add_paragraph("")
    doc.add_paragraph("second paragraph")
    doc.save(str(file_path))

    loader = SimpleDocumentLoader()
    content = loader.load_from_path(str(file_path))

    assert content == "first paragraph\nsecond paragraph"


def test_load_pdf_success(tmp_path: Path) -> None:
    fitz = pytest.importorskip("fitz")

    file_path = tmp_path / "sample.pdf"

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "hello pdf")
    pdf.save(str(file_path))
    pdf.close()

    loader = SimpleDocumentLoader()
    content = loader.load_from_path(str(file_path))

    assert "hello pdf" in content


def test_load_pdf_without_extractable_text_raises_error(tmp_path: Path) -> None:
    fitz = pytest.importorskip("fitz")

    file_path = tmp_path / "empty.pdf"

    pdf = fitz.open()
    pdf.new_page()
    pdf.save(str(file_path))
    pdf.close()

    loader = SimpleDocumentLoader()

    with pytest.raises(ValueError, match="pdf contains no extractable text"):
        loader.load_from_path(str(file_path))


def test_load_uppercase_txt_suffix_success(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.TXT"
    file_path.write_text("hello uppercase", encoding="utf-8")

    loader = SimpleDocumentLoader()
    content = loader.load_from_path(str(file_path))

    assert content == "hello uppercase"
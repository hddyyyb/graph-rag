from __future__ import annotations

from pathlib import Path

from graph_rag.application.ingest_service import IngestService
from tests.helpers import build_test_ingest_service


def test_ingest_file_txt_closed_loop(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("python fastapi graph rag", encoding="utf-8")

    service = build_test_ingest_service()

    result = service.ingest_file(
        doc_id="doc1",
        file_path=str(file_path),
    )

    assert result.doc_id == "doc1"
    assert result.chunks > 0


def test_ingest_file_docx_closed_loop(tmp_path: Path) -> None:
    docx = __import__("docx")

    file_path = tmp_path / "sample.docx"

    doc = docx.Document()
    doc.add_paragraph("graph rag system design")
    doc.save(str(file_path))

    service = build_test_ingest_service()

    result = service.ingest_file(
        doc_id="doc2",
        file_path=str(file_path),
    )

    assert result.doc_id == "doc2"
    assert result.chunks > 0


def test_ingest_file_pdf_closed_loop(tmp_path: Path) -> None:
    fitz = __import__("fitz")

    file_path = tmp_path / "sample.pdf"

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "hello graph rag")
    pdf.save(str(file_path))
    pdf.close()

    service = build_test_ingest_service()

    result = service.ingest_file(
        doc_id="doc3",
        file_path=str(file_path),
    )

    assert result.doc_id == "doc3"
    assert result.chunks > 0
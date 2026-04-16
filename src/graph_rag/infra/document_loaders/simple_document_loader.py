from __future__ import annotations
from pathlib import Path
from typing import cast
'''cast(x, T) means "treat x as type T" but does not change x's actual value.'''
from graph_rag.ports.document_loader import DocumentLoaderPort


class SimpleDocumentLoader(DocumentLoaderPort):
    def load_from_path(self, file_path: str) -> str:
        suffix = Path(file_path).suffix.lower()
        
        if suffix == ".txt":
            return self._load_txt(file_path)
        if suffix == ".pdf":
            return self._load_pdf(file_path)
        if suffix == ".docx":
            return self._load_docx(file_path)

        # PDF 的“空”其实是“解析失败”，而 TXT/DOCX 的“空”是真空内容
        raise ValueError(f"unsupported file type: {suffix or file_path}")
    
    
    def _load_txt(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    return f.read()
            except UnicodeDecodeError as e:
                raise ValueError(f"failed to decode text file: {file_path}") from e
        
    

    def _load_pdf(self, file_path: str) -> str:
        import fitz  # PyMuPDF

        parts: list[str] = []

        with fitz.open(file_path) as pdf:
            for page in pdf:
                text = cast(str, page.get_text("text"))
                if text:
                    parts.append(text)

        content = "\n".join(parts).strip()
        if not content:
            raise ValueError(f"pdf contains no extractable text: {file_path} (maybe scanned PDF)")

        return content
        
        
    def _load_docx(self, file_path: str) -> str:
        import docx

        parts: list[str] = []
        doc = docx.Document(file_path)

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                parts.append(text)

        return "\n".join(parts).strip()

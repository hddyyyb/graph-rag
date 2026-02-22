from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Document:
    doc_id: str
    text: str
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class IngestResult:
    doc_id: str
    chunks: int


@dataclass(frozen=True)
class RetrievedChunk:
    doc_id: str
    chunk_id: str
    text: str
    score: float
    source: str  # "vector" | "graph"


@dataclass(frozen=True)
class Answer:
    answer: str
    trace_id: str
    retrieval_debug: Dict[str, Any]
    citations: Optional[List[Dict[str, Any]]] = None
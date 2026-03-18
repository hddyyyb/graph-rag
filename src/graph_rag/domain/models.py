from __future__ import annotations

from dataclasses import dataclass  # A lightweight way to define classes in Python
from typing import Any, Dict, List, Optional

# These objects are used for internal communication within the application layer.
# api/schemas: HTTP request/response models (external)
# domain/models: internal business objects (internal)

@dataclass(frozen=True)
class Document:  # Represents a raw document
    doc_id: str
    text: str
    metadata: Dict[str, Any]


@dataclass(frozen=True)  
class IngestResult:  # Returned by IngestService, indicates success and number of chunks created
    doc_id: str
    chunks: int


@dataclass(frozen=True)
class RetrievedChunk:    # Returned by VectorStore(.search() returns) ; core object in GraphRAG representing a retrieved chunk 
    doc_id: str
    chunk_id: str
    text: str
    score: float
    source: str  # "vector" | "graph"


@dataclass(frozen=True)
class Answer:    # Returned by QueryService
    answer: str
    trace_id: str
    retrieval_debug: Dict[str, Any]
    citations: Optional[List[Dict[str, Any]]] = None


'''
@dataclass等价于手写这种类:
class IngestResult:
    def __init__(self, doc_id: str, chunks: int):
        self.doc_id = doc_id
        self.chunks = chunks

frozen=True: 不可变对象, 创建后不能修改
因为：它代表“结果”, 不应该被随意改动
更安全, 更可预测, 这是工程系统常用做法。
'''
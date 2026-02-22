from __future__ import annotations

from dataclasses import dataclass  # Python的一个“轻量级类定义方式”
from typing import Any, Dict, List, Optional


# 这些对象在Application层内部传递。
# api/schemas HTTP请求/响应模型（对外）
# domain/models 系统内部业务对象（对内）

@dataclass(frozen=True)
class Document:  # 表示一个原始文档
    doc_id: str
    text: str
    metadata: Dict[str, Any]


@dataclass(frozen=True)  
class IngestResult:  # IngestService返回IngestResult, 用于返回“写入成功，切了多少块”
    doc_id: str
    chunks: int


@dataclass(frozen=True)
class RetrievedChunk:    # VectorStore返回RetrievedChunk,GraphRAG的核心对象：它代表“一条检索到的片段”。vector_store.search返回的就是这个。
    doc_id: str
    chunk_id: str
    text: str
    score: float
    source: str  # "vector" | "graph"


@dataclass(frozen=True)
class Answer:    # QueryService返回Answer
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
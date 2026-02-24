from __future__ import annotations

from typing import Any, Dict, List, Optional

from graph_rag.domain.errors import ValidationError
from graph_rag.domain.models import IngestResult
from graph_rag.ports.embedding import EmbeddingProviderPort
from graph_rag.ports.graph_store import GraphStorePort
from graph_rag.ports.observability import TracePort
from graph_rag.ports.vector_store import VectorStorePort


# 负责“文档写入流程”的业务编排。

def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    '''
    切块
    '''
    t = (text or "").strip()
    if not t:
        return []
    if chunk_size <= 0:
        return [t]

    out: List[str] = []
    i = 0
    n = len(t)
    step = max(chunk_size - max(overlap, 0), 1)
    while i < n:
        out.append(t[i : i + chunk_size])
        i += step
    return out


class IngestService:    # 文档入库的业务流程控制器
    def __init__(
        self,
        vector_store: VectorStorePort,
        graph_store: GraphStorePort,
        embedder: EmbeddingProviderPort,
        trace: TracePort,
        *,
        chunk_size: int = 400,
        chunk_overlap: int = 50,
    ) -> None:
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedder = embedder
        self.trace = trace
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def ingest(
        self,
        *,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestResult:
        doc_id = (doc_id or "").strip()
        if not doc_id:
            raise ValidationError("doc_id不能为空")
        text = (text or "").strip()
        if not text:
            raise ValidationError("text不能为空")

        chunks = _chunk_text(text, self.chunk_size, self.chunk_overlap)
        if not chunks:
            raise ValidationError("切分后chunks为空")

        self.trace.bind(doc_id=doc_id)
        self.trace.event("ingest_start", chunks=len(chunks))

        embeddings = self.embedder.embed_texts(chunks)    # IngestServices初始化时候传入embedder，代码中写的是接口/父类
        self.vector_store.upsert(doc_id, chunks, embeddings)    # 调用VectorStore写入向量
        self.graph_store.upsert_document(doc_id, chunks)    # 调用GraphStore写入图结构

        self.trace.event("ingest_done", chunks=len(chunks))
        return IngestResult(doc_id=doc_id, chunks=len(chunks))
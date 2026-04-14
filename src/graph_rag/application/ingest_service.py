from __future__ import annotations

from typing import Any, Dict, List, Optional

from graph_rag.domain.errors import ValidationError
from graph_rag.domain.models import IngestResult
from graph_rag.domain.graph_models import ChunkGraphRecord

from graph_rag.ports.embedding import EmbeddingProviderPort
from graph_rag.ports.observability import TracePort
from graph_rag.ports.vector_store import VectorStorePort
from graph_rag.ports.graph_store import GraphStorePort
from graph_rag.ports.chunker import ChunkerPort

from graph_rag.common.text_utils import extract_terms

# 负责“文档写入流程”的业务编排。




class IngestService:    # 文档入库的业务流程控制器
    def __init__(
        self,
        vector_store: VectorStorePort,
        graph_store: GraphStorePort,
        embedder: EmbeddingProviderPort,
        trace: TracePort,
        chunker: ChunkerPort,
    ) -> None:
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedder = embedder
        self.trace = trace
        self.chunker = chunker

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

        chunks = self.chunker.chunk(text = text, parent_id = doc_id)
        if not chunks:
            raise ValidationError("切分后chunks为空")

        self.trace.bind(doc_id=doc_id)
        self.trace.event("ingest_start", chunks=len(chunks))

        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = self.embedder.embed_texts(chunk_texts)    # IngestServices初始化时候传入embedder，代码中写的是接口/父类
        self.vector_store.upsert(doc_id, chunk_texts, embeddings)    # 调用VectorStore写入向量
        

        graph_records: List[ChunkGraphRecord] = []

        for chunk in chunks:
            terms = extract_terms(chunk.text)
            graph_records.append(
                ChunkGraphRecord(
                    chunk_id=chunk.chunk_id,
                    doc_id=doc_id,
                    text=chunk.text,
                    terms=terms,
                )
            )

        self.graph_store.upsert_chunk_graphs(graph_records)


        self.trace.event("ingest_done", chunks=len(chunks))
        return IngestResult(doc_id=doc_id, chunks=len(chunks))
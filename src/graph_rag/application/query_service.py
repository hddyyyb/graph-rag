from __future__ import annotations

from typing import Any, Dict, List, Optional

from graph_rag.domain.errors import ValidationError
from graph_rag.domain.models import Answer, RetrievedChunk
from graph_rag.ports.embedding import EmbeddingProviderPort
from graph_rag.ports.graph_store import GraphStorePort
from graph_rag.ports.kernel import RAGKernelPort
from graph_rag.ports.observability import TracePort
from graph_rag.ports.vector_store import VectorStorePort
from graph_rag.ports.retrieval_post_processor import RetrievalPostProcessorPort

# 负责“查询流程”的业务编排
# 这是GraphRAG系统最核心的Service


class QueryService:
    def __init__(
        self,
        vector_store: VectorStorePort,
        graph_store: GraphStorePort,
        embedder: EmbeddingProviderPort,
        kernel: RAGKernelPort,
        trace: TracePort,
        post_processor: RetrievalPostProcessorPort,
        *,
        vector_top_k: int = 5,
        graph_top_k: int = 5,
    ) -> None:
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedder = embedder
        self.kernel = kernel
        self.trace = trace
        self.post_processor = post_processor 
        self.vector_top_k = vector_top_k
        self.graph_top_k = graph_top_k

    def query(
        self,
        *,
        query: str,
        top_k: Optional[int] = None,
        enable_graph: bool = True,
        enable_vector: bool = True,
        min_score: Optional[float] = 0,
    ) -> Answer:
        q = (query or "").strip()
        if not q:
            raise ValidationError("Query must not be empty")

        self.trace.bind(query=q)    # 记录trace
        self.trace.event(
            "query_start",
            enable_vector=enable_vector,
            enable_graph=enable_graph,
        )

        vector_k = top_k or self.vector_top_k
        graph_k = top_k or self.graph_top_k
        final_top_k = top_k or self.vector_top_k


        vector_chunks: List[RetrievedChunk] = []
        graph_chunks: List[RetrievedChunk] = []

        if enable_vector:
            qemb = self.embedder.embed_query(q)
            vector_chunks = self.vector_store.search(qemb, vector_k)

        if enable_graph:
            graph_chunks = self.graph_store.search(q, graph_k)

        all_chunks = vector_chunks + graph_chunks

        processed = self.post_processor.process(
            all_chunks,
            final_top_k,
            min_score,
        )

        merged = processed.chunks
        answer_text = self.kernel.generate_answer(q, merged)    # 调用Kernel生成answer

        # 构建Answer对象 (包含retrieval_debug)
        retrieval_debug: Dict[str, Any] = {
            "vector": {
                "top_k": top_k or self.vector_top_k,
                "hits": [
                    {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "score": c.score}
                    for c in vector_chunks
                ],
            },
            "graph": {
                "top_k": top_k or self.graph_top_k,
                "hits": [
                    {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "score": c.score}
                    for c in graph_chunks
                ],
            },
            "merged": {
                "count": len(merged),
                "hits": [
                    {
                        "doc_id": c.doc_id,
                        "chunk_id": c.chunk_id,
                        "score": c.score,
                        "source": c.source,
                    }
                    for c in merged[:10]
                ],
            },
        }

        trace_id = self.trace.get_trace_id()  # 获得，没有就创建uuid
        self.trace.event(
            "query_done",
            trace_id=trace_id,
            merged=len(merged),
        )

        return Answer(
            answer=answer_text,
            trace_id=trace_id,
            retrieval_debug=retrieval_debug,
            citations=processed.citations,
        )
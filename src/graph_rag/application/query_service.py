from __future__ import annotations

from typing import Any, Dict, List, Optional

from graph_rag.domain.errors import ValidationError
from graph_rag.domain.models import Answer, RetrievedChunk
from graph_rag.ports.embedding import EmbeddingProviderPort
from graph_rag.ports.graph_store import GraphStorePort
from graph_rag.ports.kernel import RAGKernelPort
from graph_rag.ports.observability import TracePort
from graph_rag.ports.vector_store import VectorStorePort


# 负责“查询流程”的业务编排
# 这是GraphRAG系统最核心的Service

def _merge_dedup(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
    seen = set()
    out: List[RetrievedChunk] = []
    for c in chunks:
        key = (c.doc_id, c.chunk_id, c.source)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    # Keep best first by score
    out.sort(key=lambda x: x.score, reverse=True)
    return out


class QueryService:
    def __init__(
        self,
        vector_store: VectorStorePort,
        graph_store: GraphStorePort,
        embedder: EmbeddingProviderPort,
        kernel: RAGKernelPort,
        trace: TracePort,
        *,
        vector_top_k: int = 5,
        graph_top_k: int = 5,
    ) -> None:
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedder = embedder
        self.kernel = kernel
        self.trace = trace
        self.vector_top_k = vector_top_k
        self.graph_top_k = graph_top_k

    def query(
        self,
        *,
        query: str,
        top_k: Optional[int] = None,
        enable_graph: bool = True,
        enable_vector: bool = True,
    ) -> Answer:
        q = (query or "").strip()
        if not q:
            raise ValidationError("query不能为空")    # 1. 校验query

        self.trace.bind(query=q)    # 2.记录trace
        self.trace.event(
            "query_start",
            enable_vector=enable_vector,
            enable_graph=enable_graph,
        )

        vector_hits: List[RetrievedChunk] = []
        graph_hits: List[RetrievedChunk] = []

        if enable_vector:        # 3. 如果enable_vector, 生成query embedding, 调用vector_store.search()
            qemb = self.embedder.embed_query(q)
            vector_hits = self.vector_store.search(qemb, top_k or self.vector_top_k)

        if enable_graph:         # 4. 如果enable_graph, 调用graph_store.search()
            graph_hits = self.graph_store.search(q, top_k or self.graph_top_k)

        merged = _merge_dedup(vector_hits + graph_hits)    # 5. 合并去重(_merge_dedup)
        answer_text = self.kernel.generate_answer(q, merged)    # 6. 调用Kernel生成answer
        
        # 7. 构建Answer对象 (包含retrieval_debug)
        retrieval_debug: Dict[str, Any] = {
            "vector": {
                "top_k": top_k or self.vector_top_k,
                "hits": [
                    {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "score": c.score}
                    for c in vector_hits
                ],
            },
            "graph": {
                "top_k": top_k or self.graph_top_k,
                "hits": [
                    {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "score": c.score}
                    for c in graph_hits
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

        # citations optional for Day2
        citations = [
            {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "source": c.source, "score": c.score}
            for c in merged[:3]
        ] if merged else []

        return Answer(
            answer=answer_text,
            trace_id=trace_id,
            retrieval_debug=retrieval_debug,
            citations=citations,
        )
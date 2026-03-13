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

from .query_option import QueryOptions, normalize_query_options





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



    def _validate_query(self, query: str) -> str:
        q = (query or "").strip()
        if not q:
            raise ValidationError("Query must not be empty")
        return q


    def _resolve_top_k_values(self, opts: QueryOptions) -> tuple[int, int, int]:
        vector_k = opts.top_k if opts.top_k is not None else self.vector_top_k
        graph_k = opts.top_k if opts.top_k is not None else self.graph_top_k
        final_top_k = opts.top_k if opts.top_k is not None else self.vector_top_k
        return vector_k, graph_k, final_top_k
    

    def _retrieve_chunks(
        self,
        *,
        q: str,
        qemb: List[float],
        opts: QueryOptions,
        vector_k: int,
        graph_k: int,
    ) -> tuple[List[RetrievedChunk], List[RetrievedChunk], List[RetrievedChunk]]:


        chunks: List[RetrievedChunk] = []
        vector_chunks: List[RetrievedChunk] = []
        graph_chunks: List[RetrievedChunk] = []

        
        if opts.enable_vector:
            vector_chunks = self.vector_store.search(
                query_embedding = qemb, 
                top_k = vector_k
                )
            chunks.extend(vector_chunks)
            self.trace.event("vector_retrieved", count = len(vector_chunks))


        if opts.enable_graph:
            graph_chunks = self.graph_store.search(
                query = q, 
                top_k = graph_k
                )
            chunks.extend(graph_chunks)
            self.trace.event("graph_retrieved", count = len(graph_chunks))

        return chunks, vector_chunks, graph_chunks
    
    def _build_retrieval_debug(
        self,
        *,
        vector_k: int,
        graph_k: int,
        vector_chunks: List[RetrievedChunk],
        graph_chunks: List[RetrievedChunk],
        merged: List[RetrievedChunk],
    ) -> Dict[str, Any]:
        
        retrieval_debug: Dict[str, Any] = {
            "vector": {
                "top_k": vector_k,
                "hits": [
                    {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "score": c.score}
                    for c in vector_chunks
                ],
            },
            "graph": {
                "top_k": graph_k,
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
        return retrieval_debug

    def query(
        self,
        *,
        query: str,
        options: Optional[QueryOptions] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        enable_graph: Optional[bool] = None,
        enable_vector: Optional[bool] = None,
    ) -> Answer:
        
        # query 第1段：参数归一化
        opts = normalize_query_options(
            options = options,
            top_k = top_k,
            min_score = min_score,
            enable_graph = enable_graph,
            enable_vector = enable_vector,
        )

        # query 第2段：输入校验
        q = self._validate_query(query)

        # query 第3段：检索参数准备
        vector_k, graph_k, final_top_k = self._resolve_top_k_values(opts)

        # query 第4段：trace开始 + embedding
        self.trace.bind(query=q)    # 记录trace
        self.trace.event(
            "query_start",
            enable_vector = opts.enable_vector,
            enable_graph = opts.enable_graph,
            top_k=opts.top_k,
            min_score=opts.min_score,
            vector_k=vector_k,
            graph_k=graph_k,
            final_top_k=final_top_k,
        )

        qemb = self.embedder.embed_query(q)


        # query 第5段：执行检索
        chunks, vector_chunks, graph_chunks = self._retrieve_chunks(
            q = q,
            qemb = qemb,
            opts = opts,
            vector_k = vector_k,
            graph_k = graph_k,
        )

        # query 第6段：后处理 + 生成答案
        processed = self.post_processor.process(
            chunks= chunks,
            top_k = final_top_k,
            min_score = opts.min_score,
        )

        merged = processed.chunks
        answer_text = self.kernel.generate_answer(query = q, contexts =  merged)    # 调用Kernel生成answer

        # query 第7段：构建 debug + 收尾返回
        retrieval_debug = self._build_retrieval_debug(
            vector_k = vector_k,
            graph_k = graph_k,
            vector_chunks = vector_chunks,
            graph_chunks = graph_chunks,
            merged = merged,
        )
        

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
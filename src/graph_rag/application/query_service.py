from __future__ import annotations

from typing import Any, Dict, List, Optional

from .errors import QueryExecutionError

from graph_rag.domain.errors import ValidationError
from graph_rag.domain.models import Answer, RetrievedChunk
from graph_rag.ports.embedding import EmbeddingProviderPort
from graph_rag.ports.graph_store import GraphStorePort
from graph_rag.ports.kernel import RAGKernelPort
from graph_rag.ports.observability import TracePort
from graph_rag.ports.vector_store import VectorStorePort
from graph_rag.ports.retrieval_post_processor import RetrievalPostProcessorPort

from .query_option import QueryOptions, normalize_query_options

import time


'''
retrieval_debug["graph"] 最终结构
{
    "query_terms": [...],
    "direct_terms": [...],
    "expanded_terms": [
        {
            "query_term": "rag",
            "expanded_term": "graph",
            "weight": 4.0,
        }
    ],
    "chunks": [
        {
            "chunk_id": "c1",
            "doc_id": "d1",
            "direct_terms": ["rag"],
            "expanded_hits": [
                {
                    "query_term": "rag",
                    "expanded_term": "graph",
                    "weight": 4.0,
                    "contribution": 2.0,
                }
            ],
            "direct_hit_count": 1,
            "expanded_hit_count": 1,
            "direct_score": 1.0,
            "expanded_score": 2.0,
            "score": 3.0,
        }
    ],
    "weights": {
        "direct_hit_weight": 1.0,
        "expanded_hit_weight": 0.5,
    },
    "scoring_formula": "score = direct_hit_count * direct_hit_weight + sum(expanded_edge_weight * expanded_hit_weight)",
    "meta": {
        "expansion_depth": 1,
        "expand_per_term_limit": 2,
        "max_expanded_terms": 10,
    },
}
'''


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
        fusion_alpha: float = 1.0,
        fusion_beta: float = 1.0,
    ) -> None:
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedder = embedder
        self.kernel = kernel
        self.trace = trace
        self.post_processor = post_processor 
        self.vector_top_k = vector_top_k
        self.graph_top_k = graph_top_k
        self.fusion_alpha = fusion_alpha
        self.fusion_beta = fusion_beta



    @staticmethod
    def _make_chunk_key(chunk: RetrievedChunk) -> tuple[str, str]:
        return (chunk.doc_id, chunk.chunk_id)


    @staticmethod
    def _safe_score(chunk: RetrievedChunk) -> float:
        if chunk.score is None:
            return 0.0
        return float(chunk.score)


    def _fuse_chunks(
        self,
        vector_chunks: list[RetrievedChunk],
        graph_chunks: list[RetrievedChunk],
    ) -> tuple[list[RetrievedChunk], dict]:
        '''
        fusion时本质上只需要做三件事-
            合并命中来源
            合并分数
            重新构造新对象
        '''
        alpha = self.fusion_alpha   # 原始权重（暂时注释）
        beta  = self.fusion_beta
        # alpha = 0.8   # 临时调整：向量分保持全权
        # beta  = 0.5   # 临时调整：图分降权，观察排序变化

        merged: dict[tuple[str, str], dict] = {}

        # 1. 先写入vector结果
        for chunk in vector_chunks:
            key = self._make_chunk_key(chunk)
            merged[key] = {
                "doc_id": chunk.doc_id,
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "vector_hit": True,
                "graph_hit": False,
                "vector_score": self._safe_score(chunk),
                "graph_score": 0.0,
            }

        # 2. 再合入graph结果
        for chunk in graph_chunks:
            key = self._make_chunk_key(chunk)
            if key not in merged:
                merged[key] = {
                    "doc_id": chunk.doc_id,
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "vector_hit": False,
                    "graph_hit": True,
                    "vector_score": 0.0,
                    "graph_score": self._safe_score(chunk),
                }
            else:
                merged[key]["graph_hit"] = True
                merged[key]["graph_score"] = self._safe_score(chunk)

        fused_chunks: list[RetrievedChunk] = []
        fusion_debug_chunks: list[dict] = []

        for item in merged.values():
            vector_hit = item["vector_hit"]
            graph_hit = item["graph_hit"]

            if vector_hit and graph_hit:
                source = "hybrid"
            elif vector_hit:
                source = "vector"
            else:
                source = "graph"

            final_score = alpha * item["vector_score"] + beta * item["graph_score"]

            fused_chunk = RetrievedChunk(
                doc_id=item["doc_id"],
                chunk_id=item["chunk_id"],
                text=item["text"],
                score=final_score,
                source=source,
            )
            fused_chunks.append(fused_chunk)

            fusion_debug_chunks.append(
                {
                    "doc_id": item["doc_id"],
                    "chunk_id": item["chunk_id"],
                    "source": source,
                    "vector_hit": vector_hit,
                    "graph_hit": graph_hit,
                    "vector_score": item["vector_score"],
                    "graph_score": item["graph_score"],
                    "final_score": final_score,
                }
            )

        fused_chunks.sort(key=lambda c: (-c.score, c.chunk_id, c.doc_id))
        fusion_debug_chunks.sort(
            key=lambda x: (-x["final_score"], x["chunk_id"], x["doc_id"])
        )

        fusion_debug = {
            "alpha": alpha,
            "beta": beta,
            "input": {
                "vector_count": len(vector_chunks),
                "graph_count": len(graph_chunks),
            },
            "output": {
                "fusion_count": len(fused_chunks),
            },
            "chunks": fusion_debug_chunks,
        }

        return fused_chunks, fusion_debug
    

    def _validate_query(self, query: str) -> str:
        q = (query or "").strip()
        if not q:
            raise ValidationError("Query must not be empty")
        return q


    def _handle_query_failure(
        self,
        *,
        stage: str,
        error: Exception,
    ) -> None:
        trace_id = self.trace.get_trace_id()
        self.trace.event(
            "query_failed",
            trace_id=trace_id,
            stage=stage,
            error_type=type(error).__name__,
            error_message=str(error),
        )
        raise QueryExecutionError(
            stage=stage,
            message=f"{stage} stage failed: {error}",
            cause=error,
        ) from error


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
    ) -> tuple[
        List[RetrievedChunk], 
        List[RetrievedChunk], 
        Optional[Dict[str, Any]],
        Dict[str, float],
        ]:


        vector_chunks: List[RetrievedChunk] = []
        graph_chunks: List[RetrievedChunk] = []
        graph_debug: Optional[Dict[str, Any]] = None

        timings: Dict[str, float] = {
            "vector_retrieval_time": 0.0,
            "graph_retrieval_time": 0.0,
        }

        # vector_retrieval
        if opts.enable_vector:
            start = time.perf_counter()
            try:
                vector_chunks = self.vector_store.search(
                    query_embedding = qemb, 
                    top_k = vector_k
                    )
            except Exception as e:
                self._handle_query_failure(
                    stage="retrieval",
                    error = e,
                )
            timings["vector_retrieval_time"] = time.perf_counter() - start
            self.trace.event("vector_retrieved", count = len(vector_chunks))
            self.trace.event(
                "retrieval_timing",
                metric="vector_retrieval_time", 
                elapsed=timings["vector_retrieval_time"],
                )

        # graph_retrieval
        if opts.enable_graph:
            start = time.perf_counter()
            try:
                graph_chunks = self.graph_store.search(
                    query = q, 
                    top_k = graph_k
                    )
                
                if hasattr(self.graph_store, "get_last_debug"): # 确定有注入
                    graph_debug = self.graph_store.get_last_debug()
                else:
                    graph_debug = None
            except Exception as e:
                self._handle_query_failure(
                    stage="retrieval",
                    error=e,
                )
            timings["graph_retrieval_time"] = time.perf_counter() - start
            self.trace.event("graph_retrieved", count = len(graph_chunks))
            self.trace.event(
                "retrieval_timing", 
                metric="graph_retrieval_time", 
                elapsed=timings["graph_retrieval_time"],
                )


        return vector_chunks, graph_chunks, graph_debug, timings


    def _build_retrieval_debug(
        self,
        *,
        vector_k: int,
        graph_k: int,
        vector_chunks: List[RetrievedChunk],
        graph_chunks: List[RetrievedChunk],
        graph_debug: Optional[Dict[str, Any]],
        fusion_debug: Dict[str, Any],
        merged: List[RetrievedChunk],
        timings: Dict[str, float],
        stats: Dict[str, int],
    ) -> Dict[str, Any]:
        
        graph_payload: Dict[str, Any] = {
            "top_k": graph_k,
            "hits": [
                {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "score": c.score}
                for c in graph_chunks
            ],
        }

        if graph_debug is not None:
            graph_payload.update(graph_debug)


        retrieval_debug: Dict[str, Any] = {
            "vector": {
                "top_k": vector_k,
                "hits": [
                    {
                        "doc_id": c.doc_id, 
                        "chunk_id": c.chunk_id, 
                        "score": c.score,
                        }
                    for c in vector_chunks
                ],
            },
            "graph": graph_payload,
            "fusion": fusion_debug,
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
            "timings": timings,
            "stats": stats,
        }
        return retrieval_debug


    def _postprocess_chunks(
        self,
        *,
        chunks: List[RetrievedChunk],
        final_top_k: int,
        min_score: Optional[float],
        timings: Dict[str, float],
        stats: Dict[str, int],
    ):
        start = time.perf_counter()
        try:
            processed = self.post_processor.process(
                chunks= chunks,
                top_k = final_top_k,
                min_score = min_score,
            )
        except Exception as e:
            self._handle_query_failure(
                stage="postprocess",
                error=e,
            )
        timings["postprocess_time"] = time.perf_counter() - start
        self.trace.event(
            "retrieval_timing",
            metric="postprocess_time",
            elapsed=timings["postprocess_time"],
        )

        stats["citation_count"] = len(processed.citations)
        return processed


    def _generate_answer_text(
        self,
        *,
        query: str,
        merged: List[RetrievedChunk],
        timings: Dict[str, float],
    ):
        start = time.perf_counter()
        try:
            answer_text = self.kernel.generate_answer(
                query = query, 
                contexts =  merged
                )    # 调用Kernel生成answer
        except Exception as e:
            self._handle_query_failure(
                stage="generation",
                error=e,
            )
        timings["llm_generation_time"] = time.perf_counter() - start
        self.trace.event(
            "retrieval_timing",
            metric="llm_generation_time",
            elapsed=timings["llm_generation_time"],
        )
        return answer_text



    def _build_answer(
        self,
        *,
        answer_text: str,
        processed,
        vector_k: int,
        graph_k: int,
        vector_chunks,
        graph_chunks,
        graph_debug,
        fusion_debug,
        merged,
        timings,
        stats,
    ):
        """
        参数说明:
        - answer_text: 生成的答案文本
        - processed: post_processor的输出, 包含最终用于生成答案的chunks和引用信息
        - vector_k / graph_k: 实际用于检索的top_k参数值
        - vector_chunks / graph_chunks: 原始的向量检索和图检索结果
        - graph_debug: 图检索的调试信息(如果有的话)
        - merged: 最终用于生成答案的chunks列表(经过合并和排序)
        - timings: 各个阶段的耗时统计
        - stats: 各种计数统计(如检索到的chunk数量、引用数量等)

        _build_retrieval_debug的作用及与processed的区别:
        - _build_retrieval_debug负责构建retrieval_debug字典, 包含完整检索调试信息:
        包括原始vector/graph检索结果、最终merged chunks、以及timings和stats
        主要用于帮助开发者理解查询流程, 尤其是retrieval阶段的行为
        - processed是post_processor的直接输出, 是结构化结果:
        包含最终用于生成答案的chunks和citations
        - 区别: processed关注"结果", _build_retrieval_debug覆盖"全过程"(retrieval -> postprocess -> stats)

        二者关系:
        - processed中的chunks对应retrieval_debug中的merged结果
        - processed中的citations对应stats["citation_count"]的一部分
        - retrieval_debug额外包含:
        原始检索结果(vector_chunks / graph_chunks)、graph_debug、timings、stats等全过程信息

        最终Answer对象组成:
        - answer_text: LLM生成的答案
        - trace_id: 当前查询的追踪ID
        - retrieval_debug: 由_build_retrieval_debug构建的完整调试信息
        - citations: 来自processed中的引用信息

        总结:
        - processed = 用于生成答案的数据
        - retrieval_debug = 用于理解系统行为和调试的数据
        """
        retrieval_debug = self._build_retrieval_debug(
            vector_k = vector_k,
            graph_k = graph_k,
            vector_chunks = vector_chunks,
            graph_chunks = graph_chunks,
            graph_debug = graph_debug,
            fusion_debug=fusion_debug,
            merged = merged,
            timings = timings,
            stats = stats,
        )
        

        trace_id = self.trace.get_trace_id()  # obtain trace id (generate UUID if absent)
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
        
        # normalize query parameters
        opts = normalize_query_options(
            options = options,
            top_k = top_k,
            min_score = min_score,
            enable_graph = enable_graph,
            enable_vector = enable_vector,
        )

        q = self._validate_query(query)    # validate input query
        
        vector_k, graph_k, final_top_k = self._resolve_top_k_values(opts)    # prepare retrieval parameters

        timings: Dict[str, float] = {
            "embedding_time": 0.0,
            "vector_retrieval_time": 0.0,
            "graph_retrieval_time": 0.0,
            "postprocess_time": 0.0,
            "llm_generation_time": 0.0,
        }

        stats: Dict[str, int] = {
            "vector_count" : 0,
            "graph_count" : 0,
            "fusion_count" : 0,
            "citation_count" : 0,
        }
        

        # start trace + compute embedding
        self.trace.bind(query=q)    # attach query to trace context
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
        
        # embedding_time
        start = time.perf_counter()

        try:
            qemb = self.embedder.embed_query(q)
        except Exception as e:
            self._handle_query_failure(
                stage="embedding",
                error=e,
            )



        timings["embedding_time"] = time.perf_counter() - start
        self.trace.event(
            "retrieval_timing", 
            metric="embedding_time", 
            elapsed=timings["embedding_time"],
            )


        # perform retrieval
        vector_chunks, graph_chunks, graph_debug, retrieval_timings  = self._retrieve_chunks(
            q = q,
            qemb = qemb,
            opts = opts,
            vector_k = vector_k,
            graph_k = graph_k,
        )
        timings.update(retrieval_timings)

        stats["vector_count"] = len(vector_chunks)
        stats["graph_count"] = len(graph_chunks)
        
        fused_chunks, fusion_debug = self._fuse_chunks(
            vector_chunks=vector_chunks,
            graph_chunks=graph_chunks,
        )

        stats["fusion_count"] = len(fused_chunks)

        # post-processing & postprocess_time
        processed = self._postprocess_chunks(
            chunks=fused_chunks,
            final_top_k=final_top_k,
            min_score=opts.min_score,
            timings=timings,
            stats=stats,
        )

        merged = processed.chunks

        # llm_generation_time
        answer_text = self._generate_answer_text(
            query = q,
            merged = merged,
            timings = timings,
            )

        # build debug info + finalize response
        return self._build_answer(
            answer_text = answer_text,
            processed = processed,
            vector_k = vector_k,
            graph_k = graph_k,
            graph_debug = graph_debug,
            fusion_debug = fusion_debug,
            vector_chunks = vector_chunks,
            graph_chunks = graph_chunks,
            merged = merged,
            timings = timings,
            stats = stats,
        )


        
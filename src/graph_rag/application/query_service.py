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
        List[RetrievedChunk], 
        Optional[Dict[str, Any]],
        Dict[str, float],
        ]:

        chunks: List[RetrievedChunk] = []
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
            chunks.extend(vector_chunks)
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
                graph_debug = self.graph_store.get_last_debug()
            except Exception as e:
                self._handle_query_failure(
                    stage="retrieval",
                    error=e,
                )
            timings["graph_retrieval_time"] = time.perf_counter() - start
            chunks.extend(graph_chunks)
            self.trace.event("graph_retrieved", count = len(graph_chunks))
            self.trace.event(
                "retrieval_timing", 
                metric="graph_retrieval_time", 
                elapsed=timings["graph_retrieval_time"],
                )


        return chunks, vector_chunks, graph_chunks, graph_debug, timings


    def _build_retrieval_debug(
        self,
        *,
        vector_k: int,
        graph_k: int,
        vector_chunks: List[RetrievedChunk],
        graph_chunks: List[RetrievedChunk],
        graph_debug: Optional[Dict[str, Any]],
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
                    {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "score": c.score}
                    for c in vector_chunks
                ],
            },
            "graph": graph_payload,
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
        chunks,
        final_top_k: int,
        min_score,
        timings,
        stats,
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
        merged,
        timings,
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
        merged,
        timings,
        stats,
    ):
        retrieval_debug = self._build_retrieval_debug(
            vector_k = vector_k,
            graph_k = graph_k,
            vector_chunks = vector_chunks,
            graph_chunks = graph_chunks,
            graph_debug = graph_debug,
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
            "merged_count" : 0,
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
        chunks, vector_chunks, graph_chunks, graph_debug, retrieval_timings  = self._retrieve_chunks(
            q = q,
            qemb = qemb,
            opts = opts,
            vector_k = vector_k,
            graph_k = graph_k,
        )
        timings.update(retrieval_timings)

        stats["vector_count"] = len(vector_chunks)
        stats["graph_count"] = len(graph_chunks)
        stats["merged_count"] = len(chunks)
        

        # post-processing & postprocess_time
        processed = self._postprocess_chunks(
            chunks=chunks,
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
            vector_chunks = vector_chunks,
            graph_chunks = graph_chunks,
            merged = merged,
            timings = timings,
            stats = stats,
        )


        
from __future__ import annotations

from typing import List, Optional, Any

from graph_rag.domain.models import RetrievedChunk
from graph_rag.application.query_service import QueryService

from graph_rag.ports.vector_store import VectorStorePort, SearchOptions

from graph_rag.ports.graph_store import GraphStorePort
from graph_rag.ports.embedding import EmbeddingProviderPort
from graph_rag.ports.kernel import RAGKernelPort
from graph_rag.ports.observability import TracePort

from graph_rag.infra.adapters import DefaultRetrievalPostProcessor



class FakeVectorStore(VectorStorePort):
    def search(
            self,
            query_embedding: List[float],
            top_k: int,
            options: Optional[SearchOptions] = None,
            filter_doc_id: Optional[str] = None,
            min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        duplicate_low = RetrievedChunk(doc_id = "doc_1", chunk_id = "chunk_1", source = "vector", score = 0.90, text = 'text 01')
        normal_chunk_1 = RetrievedChunk(doc_id = "doc_2", chunk_id = "chunk_2", source = "vector", score = 0.88, text = 'text 02')
        duplicate_high = RetrievedChunk(doc_id = "doc_1", chunk_id = "chunk_1", source = "vector", score = 0.92, text = 'text 03')
        return [duplicate_low, normal_chunk_1, duplicate_high]

class FakeGraphStore(GraphStorePort):
    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        normal_chunk_2 = RetrievedChunk(doc_id = "doc_3", chunk_id = "chunk_3", source = "graph", score = 0.85, text = 'text 04')
        return [normal_chunk_2]
        

class FakeEmbedder(EmbeddingProviderPort):
    def embed_query(self, query: str) -> List[float]:
        return [0.0,0.0,0.0]

class FakeKernel(RAGKernelPort):
    def __init__(self) -> None:
        self.last_query = ""
        self.last_chunks = []
        self.reply = "fake-answer"

    def generate_answer(self, query: str, contexts: List[RetrievedChunk]):
        self.last_query = query
        self.last_chunks = contexts
        return self.reply

    
class FakeTrace(TracePort):
    def __init__(self) -> None:
        self._trace_id = "trace_test_999"
        self._fields = {}

    def get_trace_id(self) -> str:
        return self._trace_id

    def set_trace_id(self, trace_id: str) -> None:
        self._trace_id = trace_id

    def bind(self, **fields: Any) -> None:
        self._fields.update(fields)

    def event(self, name: str, **fields: Any) -> None:
        pass

    def get_bound_fields(self) -> Dict[str, Any]:
        return dict(self._fields)


def test_query_service_uses_post_processed_chunks_and_citations():
    vector_store = FakeVectorStore()
    graph_store = FakeGraphStore()
    embedder = FakeEmbedder()
    kernel = FakeKernel()
    trace = FakeTrace()
    post_processor = DefaultRetrievalPostProcessor()

    service = QueryService(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        kernel=kernel,
        trace=trace,
        post_processor=post_processor,
        vector_top_k=5,
        graph_top_k=5,
    )

    result = service.query(
        query="GraphRAG是什么?",
        top_k=2,
        enable_vector=True,
        enable_graph=True,
    )

    assert result.answer == "fake-answer"
    assert result.trace_id == "trace_test_999"

    citation_keys = [(item['doc_id'], item['chunk_id']) for item in result.citations]
    assert citation_keys == [("doc_1", "chunk_1"), ("doc_2", "chunk_2")]   

    kernel_keys =[(chunk.doc_id, chunk.chunk_id) for chunk in kernel.last_chunks]  # [RetrievedChunk]
    assert kernel_keys ==  [("doc_1", "chunk_1"), ("doc_2", "chunk_2")]  

    assert result.retrieval_debug["merged"]["count"] == 2
from __future__ import annotations


from graph_rag.application import IngestService, QueryService

from graph_rag.infra.adapters import (
    DefaultRetrievalPostProcessor,
    InMemoryGraphStore,
    InMemoryVectorStore,
    SentenceTransformerEmbeddingProvider,
    FakeKernel,
    FixedLengthChunker,
)
from graph_rag.infra.observability.fake_trace import FakeTrace
from tests.helpers import build_test_service, build_test_ingest_service

def test_graph_retrieval_closed_loop_with_graph_only():
    
    vector_store = InMemoryVectorStore()
    graph_store = InMemoryGraphStore()

    embedder = SentenceTransformerEmbeddingProvider()

    kernel = FakeKernel()
    trace = FakeTrace()
    post_processor = DefaultRetrievalPostProcessor()
    chunker = FixedLengthChunker()

    ingest_service = build_test_ingest_service(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        trace=trace,
        chunker=chunker,
    )

    query_service = QueryService(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        kernel=kernel,
        trace=trace,
        post_processor=post_processor,
        vector_top_k=10,
        graph_top_k=5,
    )

    texts = [
        "python fastapi sqlite vector retrieval",
        "neo4j graph entity relation retrieval",
    ]

    for i, text in enumerate(texts, start=1):
        ingest_service.ingest(
            doc_id=f"doc_{i}",
            text=text,
        )

    result = query_service.query(
        query="graph retrieval",
        top_k=2,
        enable_vector=False,
        enable_graph=True,
        min_score=0.0,
    )

    assert len(result.citations) == 2
    assert all(c["source"] == "graph" for c in result.citations)

from __future__ import annotations

from typing import Optional, List

from graph_rag.domain.models import RetrievedChunk

from graph_rag.infra.adapters import DefaultRetrievalPostProcessor
from graph_rag.infra.adapters import FakeEmbeddingV2, FakeKernel
from graph_rag.infra.observability.fake_trace import FakeTrace

from graph_rag.application.query_service import QueryService

from graph_rag.ports.vector_store import VectorStorePort, SearchOptions
from graph_rag.ports.graph_store import GraphStorePort

from tests.fakes.fake_vector_store import FakeVectorStore, FakeVectorStore_only_graph, FakeVectorStore_only_vector, FakeVectorStoreMinScore
from tests.fakes.fake_graph_store import FakeGraphStore, FakeGraphStore_only_graph, FakeGraphStore_only_vector, FakeGraphStoreMinScore



def test_hybrid_vector_and_graph():
    vector_store = FakeVectorStore()
    graph_store = FakeGraphStore()
    embedder = FakeEmbeddingV2()
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
        query="test query",
        top_k=5,
        enable_vector=True,
        enable_graph=True,
        min_score=0.0,
    )
    
    assert len(result.citations) == 3
    assert result.citations[0]["score"] == 0.95
    assert any(c["source"] == "graph" for c in result.citations)
    

def test_hybrid_vector_and_graph_min_score():
    vector_store = FakeVectorStoreMinScore()
    graph_store = FakeGraphStoreMinScore()
    embedder = FakeEmbeddingV2()
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
        query="test query",
        top_k=5,
        enable_vector=True,
        enable_graph=True,
        min_score=0.5,
    )
    
    assert len(result.citations) == 2
    assert all(c["score"] >= 0.5 for c in result.citations)
    assert any(c["source"] == "vector" for c in result.citations)
    assert any(c["source"] == "graph" for c in result.citations)



def test_only_vector():
    vector_store = FakeVectorStore_only_vector()
    graph_store = FakeGraphStore_only_vector()
    embedder = FakeEmbeddingV2()
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
        query="test query",
        top_k=5,
        enable_vector=True,
        enable_graph=True,
        min_score=0.5,
    )
    
    assert len(result.citations) == 1
    assert result.citations[0]["source"] == "vector"
    assert result.answer == "fake-answer"


def test_only_graph():
    vector_store = FakeVectorStore_only_graph()
    graph_store = FakeGraphStore_only_graph()
    embedder = FakeEmbeddingV2()
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
        query="test query",
        top_k=5,
        enable_vector=True,
        enable_graph=True,
        min_score=0.5,
    )
    
    assert len(result.citations) == 1
    assert result.citations[0]["source"] == "graph"
    assert result.answer == "fake-answer"
from __future__ import annotations

import pytest

from tests.helpers import build_test_service
from graph_rag.application import QueryExecutionError

from graph_rag.domain.errors import ValidationError

from graph_rag.ports.vector_store import VectorStorePort
from graph_rag.ports.graph_store import GraphStorePort

from graph_rag.ports.kernel import RAGKernelPort

class FailingEmbedding:
    def embed_query(self, query: str):
        raise RuntimeError("embedding service down")


class FailingVectorStore(VectorStorePort):
    def search(self, query_embedding, top_k, options = None, filter_doc_id = None, min_score = None):
        raise RuntimeError("vector store down")


class FailingGraphStore(GraphStorePort):
    def search(self, query, top_k):
        raise RuntimeError("graph store down")
    

class FailingPostProcessor:
    def process(self, chunks, top_k, min_score=None):
        raise RuntimeError("postprocess failed")


class FailingGeneration(RAGKernelPort):
    def generate_answer(self, query, contexts):
        raise RuntimeError("generation failed")

def test_query_embedding_failure():
    service = build_test_service(
        embedder = FailingEmbedding()
        )

    with pytest.raises(QueryExecutionError) as exc:
        service.query(query = "hello")

    assert exc.value.stage == "embedding"
    assert exc.value.cause is not None

def test_query_validation_error_not_wrapped():
    service = build_test_service()

    with pytest.raises(ValidationError):
        service.query(query="   ")

def test_query_vector_retrieval_failure():
    service = build_test_service(
        vector_store=FailingVectorStore()
    )

    with pytest.raises(QueryExecutionError) as exc:
        service.query(query="hello", enable_graph=False)
    
    assert exc.value.stage == "retrieval"

def test_query_graph_retrieval_failure():
    service = build_test_service(
        graph_store=FailingGraphStore()
    )

    with pytest.raises(QueryExecutionError) as exc:
        service.query(query="hello", enable_vector=False)
    
    assert exc.value.stage == "retrieval"

def test_postprocess_failure():
    service = build_test_service(
        post_processor=FailingPostProcessor()
    )

    with pytest.raises(QueryExecutionError) as exc:
        service.query(query="hello")
    
    assert exc.value.stage == "postprocess"


def test_generation_failure():
    service = build_test_service(
        kernel=FailingGeneration()
    )

    with pytest.raises(QueryExecutionError) as exc:
        service.query(query="hello")
    
    assert exc.value.stage == "generation"
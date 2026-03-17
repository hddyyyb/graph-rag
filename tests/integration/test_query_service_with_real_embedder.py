from __future__ import annotations

from tests.helpers import build_test_service

from graph_rag.infra.adapters import SentenceTransformerEmbeddingProvider

def test_query_service_works_with_real_sentence_transformer_embedder():
    
    service = build_test_service(
        embedder= SentenceTransformerEmbeddingProvider()
    )
    answer = service.query(query="hello")

    assert answer.answer is not None
    assert answer.trace_id is not None
    assert answer.retrieval_debug is not None

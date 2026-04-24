from __future__ import annotations

import pytest

from graph_rag.domain.errors import ValidationError


from tests.helpers import build_test_service
from tests.fakes.fake_vector_store import FakeVectorStore12counts


def test_query_empty_query_raises_validation_error():
    service = build_test_service()
    with pytest.raises(ValidationError):
        service.query(
            query= " "
        )

def test_query_disable_graph_keeps_graph_hits_empty():
    service = build_test_service()
    response = service.query(
        query= "Hello",
        enable_vector=True,
        enable_graph=False,
    )
        
    assert response.retrieval_debug["vector"]["hits"] != []
    assert response.retrieval_debug["graph"]["hits"] == []


def test_query_merged_debug_hits_are_limited_to_10():
    service = build_test_service(
        vector_store=FakeVectorStore12counts(),
        vector_top_k=12,
        graph_top_k=1,
        )
    response = service.query(
        query= "Hello",
    )
       
    assert response.retrieval_debug["merged"]["count"] == 12
    assert len(response.retrieval_debug["merged"]["hits"]) == 10

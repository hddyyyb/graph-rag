from __future__ import annotations

from tests.helpers import build_test_service
from graph_rag.application.query_option import QueryOptions, normalize_query_options


def test_normalize_query_options_defaults():
    opts = normalize_query_options()

    assert opts.top_k is None
    assert opts.min_score is None
    assert opts.enable_vector is True
    assert opts.enable_graph is True



def test_normalize_query_options_from_options():
    base = QueryOptions(top_k=3, min_score=0.1, enable_graph= False)
    opts = normalize_query_options(options=base)

    assert opts.top_k == 3
    assert opts.min_score == 0.1
    assert opts.enable_graph is False


def test_normalize_query_options_from_legacy_args():
    opts = normalize_query_options(
        top_k= 2,
        enable_graph=False,
    )
    
    assert opts.top_k == 2
    assert opts.enable_graph is False


def test_normalize_query_options_legacy_override_options():
    base = QueryOptions(top_k=5, enable_graph=True)

    opts = normalize_query_options(
        options=base,
        top_k=2,
        enable_graph=False,
    )

    assert opts.top_k == 2
    assert opts.enable_graph is False


def test_query_legacy_args():
    service = build_test_service()

    result = service.query(
        query="hello",
        top_k = 2,
        enable_graph= False,
    )

    assert result is not None


def test_query_options():
    service = build_test_service()
    opts = QueryOptions(
        top_k=2,
        enable_graph=False,
        )
    
    result = service.query(
        query='hello',
        options=opts,
    )

    assert result is not None


def test_query_legacy_override_options():
    service = build_test_service()
    opts = QueryOptions(
        top_k=5,
        enable_graph=False,
        )
    
    result = service.query(
        query='hello',
        options=opts,
        top_k=2,
        enable_graph=False,
    )

    assert result is not None


def test_query_options_not_overridden():
    service = build_test_service()

    opts = QueryOptions(
        enable_graph=False,
        min_score=0.8,
    )

    result = service.query(
        query="hello",
        options=opts,
    )
    score = [c["score"] for c in result.citations]
    assert all(s >=0.8 for s in score)
    

def test_query_disable_vector_does_not_crash():
    service = build_test_service()

    result = service.query(
        query="hello",
        enable_vector=False,
    )

    assert result is not None


def test_query_retrieval_stats():
    service = build_test_service()
    answer = service.query(
        query="hello",
    )

    assert answer.retrieval_debug is not None
    stats = answer.retrieval_debug["stats"]

    assert stats["vector_count"] == 2
    assert stats["graph_count"] == 1
    assert stats["fusion_count"] == 3
    assert stats["citation_count"] == 3
from __future__ import annotations

from graph_rag.application import IngestService, QueryService

from graph_rag.infra.adapters import (
    DefaultRetrievalPostProcessor,
    InMemoryGraphStore,
    SQLiteVectorStore,
    SentenceTransformerEmbeddingProvider,
    FakeKernel,
    FixedLengthChunker,
)
from graph_rag.infra.observability.fake_trace import FakeTrace


def test_real_sqlite_vector_only_closed_loop(tmp_path):
    # 1) real sqlite backend
    db_path = str(tmp_path / "real_vector_only.db")
    vector_store = SQLiteVectorStore(db_path)

    # 2) graph disabled / non-participating
    graph_store = InMemoryGraphStore()

    # 3) real embedding
    embedder = SentenceTransformerEmbeddingProvider(
        model_name_or_path="sentence-transformers/all-MiniLM-L6-v2",
        normalize_embeddings=True,
    )

    # 4) same test-style kernel / trace as existing service tests
    kernel = FakeKernel()
    trace = FakeTrace()
    post_processor = DefaultRetrievalPostProcessor()
    chunker = FixedLengthChunker()
    ingest_service = IngestService(
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
        vector_top_k=5,
        graph_top_k=5,
    )

    # 5) ingest two clearly different docs
    ingest_service.ingest(
        doc_id="doc_graph",
        text="Graph neural networks are used for node classification.",
    )
    ingest_service.ingest(
        doc_id="doc_food",
        text="Fresh oranges and apples are sold in the market.",
    )

    # 6) query with vector only
    result = query_service.query(
        query="graph node classification",
        top_k=3,
        enable_vector=True,
        enable_graph=False,
        min_score=0.0,
    )

    # 7) core assertions: real retrieval happened, and source is vector only
    assert len(result.citations) > 0
    assert all(c["source"] == "vector" for c in result.citations)

    # Optional but recommended: the retrieved text/doc should lean to graph doc
    assert any(c.get("doc_id") == "doc_graph" for c in result.citations)


    # Optional debug assertions if your retrieval_debug structure already exposes them
    if result.retrieval_debug is not None:
        stats = result.retrieval_debug.get("stats", {})
        assert stats.get("graph_retrieved", 0) == 0

        timings = result.retrieval_debug.get("timings", {})
        assert timings.get("vector_retrieval_time", 0.0) >= 0.0
        assert timings.get("graph_retrieval_time", 0.0) >= 0.0


def test_real_sqlite_vector_top_k_closed_loop(tmp_path):
    db_path = str(tmp_path / "real_vector_topk.db")
    vector_store = SQLiteVectorStore(db_path)
    graph_store = InMemoryGraphStore()

    embedder = SentenceTransformerEmbeddingProvider(
        model_name_or_path="sentence-transformers/all-MiniLM-L6-v2",
        normalize_embeddings=True,
    )

    kernel = FakeKernel()
    trace = FakeTrace()
    post_processor = DefaultRetrievalPostProcessor()

    ingest_service = IngestService(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        trace=trace,
        chunker=FixedLengthChunker(),
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
        "Graph neural networks for node classification.",
        "Node classification on citation graphs.",
        "Graph embeddings improve retrieval quality.",
        "Fresh fruit and vegetable market prices.",
    ]

    for i, text in enumerate(texts, start=1):
        ingest_service.ingest(
            doc_id=f"doc_{i}",
            text=text,
        )

    result = query_service.query(
        query="graph node classification",
        top_k=2,
        enable_vector=True,
        enable_graph=False,
        min_score=0.0,
    )

    assert len(result.citations) == 2
    assert all(c["source"] == "vector" for c in result.citations)

    scores = [c["score"] for c in result.citations]
    assert scores == sorted(scores, reverse=True)

    debug = result.retrieval_debug
    assert debug is not None

    stats = debug.get("stats", {})
    assert stats.get("vector_count", 0) >= 2
    assert stats.get("graph_count", 0) == 0



def test_real_sqlite_vector_min_score_closed_loop(tmp_path):
    db_path = str(tmp_path / "real_vector_minscore.db")
    vector_store = SQLiteVectorStore(db_path)
    graph_store = InMemoryGraphStore()

    embedder = SentenceTransformerEmbeddingProvider(
        model_name_or_path="sentence-transformers/all-MiniLM-L6-v2",
        normalize_embeddings=True,
    )

    kernel = FakeKernel()
    trace = FakeTrace()
    post_processor = DefaultRetrievalPostProcessor()

    ingest_service = IngestService(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        trace=trace,
        chunker=FixedLengthChunker(),
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
        "Graph neural networks for node classification.",
        "Node classification in graph machine learning.",
        "Fresh fruit and vegetable prices in the local market.",
    ]

    for i, text in enumerate(texts, start=1):
        ingest_service.ingest(
            doc_id=f"doc_{i}",
            text=text,
        )

    loose_result = query_service.query(
        query="graph node classification",
        top_k=5,
        enable_vector=True,
        enable_graph=False,
        min_score=0.0,
    )

    strict_result = query_service.query(
        query="graph node classification",
        top_k=5,
        enable_vector=True,
        enable_graph=False,
        min_score=0.5,   # 若你本地分数分布不合适，再调成0.4或0.6
    )

    assert len(loose_result.citations) > 0
    assert len(strict_result.citations) <= len(loose_result.citations)

    assert all(c["source"] == "vector" for c in loose_result.citations)
    assert all(c["source"] == "vector" for c in strict_result.citations)

    assert all(c["score"] >= 0.5 for c in strict_result.citations)

    loose_debug = loose_result.retrieval_debug
    strict_debug = strict_result.retrieval_debug

    assert loose_debug is not None
    assert strict_debug is not None

    loose_stats = loose_debug.get("stats", {})
    strict_stats = strict_debug.get("stats", {})

    assert loose_stats.get("graph_count", 0) == 0
    assert strict_stats.get("graph_count", 0) == 0
    assert loose_stats.get("vector_count", 0) > 0
    assert strict_stats.get("vector_count", 0) > 0
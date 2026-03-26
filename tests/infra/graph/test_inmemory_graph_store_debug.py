from graph_rag.domain.graph_models import ChunkGraphRecord
from graph_rag.infra.adapters import InMemoryGraphStore


def test_inmemory_graph_search_returns_debug():
    store = InMemoryGraphStore(
        expand_per_term_limit=2,
        direct_hit_weight=1.0,
        expanded_hit_weight=0.5,
    )

    store.upsert_chunk_graphs([
        ChunkGraphRecord(
            chunk_id="c1",
            doc_id="doc1",
            text="python fastapi tutorial",
            terms=["python", "fastapi", "tutorial"],
        ),
        ChunkGraphRecord(
            chunk_id="c2",
            doc_id="doc1",
            text="fastapi backend service",
            terms=["fastapi", "backend", "service"],
        ),
    ])

    result = store.search("python", top_k=5)
    debug = store.get_last_debug()

    assert isinstance(result, list)
    assert debug is not None
    assert debug["query"] == "python"
    assert "python" in debug["direct_terms"]
    assert isinstance(debug["expanded_terms"], list)
    assert isinstance(debug["chunks"], list)
    assert len(result) == len(debug["chunks"])

    first = debug["chunks"][0]
    assert "chunk_id" in first
    assert "doc_id" in first
    assert "direct_hit_count" in first
    assert "expanded_hit_count" in first
    assert "score" in first


def test_inmemory_graph_debug_score_matches_chunk_score():
    store = InMemoryGraphStore(
        expand_per_term_limit=2,
        direct_hit_weight=1.0,
        expanded_hit_weight=0.5,
    )

    store.upsert_chunk_graphs([
        ChunkGraphRecord(
            chunk_id="c1",
            doc_id="doc1",
            text="python fastapi tutorial",
            terms=["python", "fastapi", "tutorial"],
        ),
        ChunkGraphRecord(
            chunk_id="c2",
            doc_id="doc1",
            text="fastapi backend service",
            terms=["fastapi", "backend", "service"],
        ),
    ])

    result = store.search("python", top_k=5)
    debug = store.get_last_debug()

    assert debug is not None

    debug_map = {item["chunk_id"]: item for item in debug["chunks"]}

    for hit in result:
        dbg = debug_map[hit.chunk_id]
        expected_score = (
            dbg["direct_hit_count"] * 1.0
            + dbg["expanded_hit_count"] * 0.5
        )
        assert dbg["score"] == expected_score
        assert hit.score == dbg["score"]
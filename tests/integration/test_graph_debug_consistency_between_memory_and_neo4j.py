import pytest

from graph_rag.domain.graph_models import ChunkGraphRecord


@pytest.mark.integration
def test_graph_debug_consistency_between_memory_and_neo4j(memory_store, neo4j_store):
    records = [
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
    ]

    memory_store.upsert_chunk_graphs(records)
    neo4j_store.upsert_chunk_graphs(records)

    memory_result = memory_store.search("python", top_k=10)
    neo4j_result = neo4j_store.search("python", top_k=10)

    memory_debug = memory_store.get_last_debug()
    neo4j_debug = neo4j_store.get_last_debug()

    assert isinstance(memory_result, list)
    assert isinstance(neo4j_result, list)
    assert memory_debug is not None
    assert neo4j_debug is not None

    assert "direct_terms" in memory_debug
    assert "expanded_terms" in memory_debug
    assert "chunks" in memory_debug

    assert "direct_terms" in neo4j_debug
    assert "expanded_terms" in neo4j_debug
    assert "chunks" in neo4j_debug

    memory_map = {item["chunk_id"]: item for item in memory_debug["chunks"]}
    neo4j_map = {item["chunk_id"]: item for item in neo4j_debug["chunks"]}

    assert set(memory_map.keys()) == set(neo4j_map.keys())

    for chunk_id in memory_map:
        assert memory_map[chunk_id]["direct_hit_count"] == neo4j_map[chunk_id]["direct_hit_count"]
        assert memory_map[chunk_id]["expanded_hit_count"] == neo4j_map[chunk_id]["expanded_hit_count"]
        assert memory_map[chunk_id]["score"] == neo4j_map[chunk_id]["score"]
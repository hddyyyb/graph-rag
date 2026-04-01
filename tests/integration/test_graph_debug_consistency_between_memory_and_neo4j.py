import pytest

from graph_rag.domain.graph_models import ChunkGraphRecord


@pytest.mark.integration
def test_graph_debug_shape_consistency_between_memory_and_neo4j(memory_store, neo4j_store):
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



import pytest

from graph_rag.domain.graph_models import ChunkGraphRecord
from graph_rag.infra.adapters.in_memory_graph_store import InMemoryGraphStore
from graph_rag.infra.adapters.neo4j_graph_store import Neo4jGraphStore


@pytest.mark.integration
def test_graph_debug_weight_ranking_consistency_between_memory_and_neo4j(neo4j_driver, neo4j_config):
    with neo4j_driver.session(database=neo4j_config["neo4j_database"]) as session:
        session.run("MATCH (n) DETACH DELETE n")

    memory_store = InMemoryGraphStore(
        expand_per_term_limit=5,
        direct_hit_weight=1.0,
        expanded_hit_weight=0.5,
        max_expanded_terms=10,
    )
    neo4j_store = Neo4jGraphStore(
        driver=neo4j_driver,
        database=neo4j_config["neo4j_database"],
        expand_per_term_limit=5,
        direct_hit_weight=1.0,
        expanded_hit_weight=0.5,
        max_expanded_terms=10,
    )

    records = [
        ChunkGraphRecord(doc_id="d1", chunk_id="c1", text="graph only", terms=["graph"]),
        ChunkGraphRecord(doc_id="d2", chunk_id="c2", text="ranking only", terms=["ranking"]),
        ChunkGraphRecord(doc_id="d3", chunk_id="c3", text="rag graph", terms=["rag", "graph"]),
        ChunkGraphRecord(doc_id="d4", chunk_id="c4", text="rag graph", terms=["rag", "graph"]),
        ChunkGraphRecord(doc_id="d5", chunk_id="c5", text="rag ranking", terms=["rag", "ranking"]),
    ]

    memory_store.upsert_chunk_graphs(records)
    neo4j_store.upsert_chunk_graphs(records)

    memory_store.search("rag", top_k=10)
    neo4j_store.search("rag", top_k=10)

    memory_debug = memory_store.get_last_debug()
    neo4j_debug = neo4j_store.get_last_debug()

    assert memory_debug is not None
    assert neo4j_debug is not None

    assert memory_debug["expanded_terms"][0]["expanded_term"] == neo4j_debug["expanded_terms"][0]["expanded_term"]

    mem_chunk_scores = {item["chunk_id"]: item["score"] for item in memory_debug["chunks"]}
    neo_chunk_scores = {item["chunk_id"]: item["score"] for item in neo4j_debug["chunks"]}

    assert mem_chunk_scores["c1"] > mem_chunk_scores["c2"]
    assert neo_chunk_scores["c1"] > neo_chunk_scores["c2"]
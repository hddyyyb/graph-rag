from graph_rag.domain.graph_models import ChunkGraphRecord
from graph_rag.infra.adapters import InMemoryGraphStore


def test_in_memory_graph_store_search_returns_graph_chunks():
    store = InMemoryGraphStore()

    store.upsert_chunk_graphs([
        ChunkGraphRecord(
            chunk_id="doc_1#0",
            doc_id="doc_1",
            text="python fastapi sqlite vector retrieval",
            terms=["python", "fastapi", "sqlite", "vector", "retrieval"],
        ),
        ChunkGraphRecord(
            chunk_id="doc_2#0",
            doc_id="doc_2",
            text="neo4j graph entity relation retrieval",
            terms=["neo4j", "graph", "entity", "relation", "retrieval"],
        ),
    ])

    results = store.search("graph retrieval", top_k=5)

    assert len(results) >= 1
    assert results[0].source == "graph"
    assert any(r.chunk_id == "doc_2#0" for r in results)


def test_in_memory_graph_store_builds_nodes_and_edges():
    store = InMemoryGraphStore()

    store.upsert_chunk_graphs([
        ChunkGraphRecord(
            chunk_id="doc_1#0",
            doc_id="doc_1",
            text="graph retrieval relation",
            terms=["graph", "retrieval", "relation"],
        )
    ])

    assert "graph" in store.nodes_by_name
    assert "retrieval" in store.nodes_by_name
    assert len(store.edges_by_pair) > 0


def test_search_includes_expanded_term_hits():
    # 测试：扩展term能召回expanded hit
    store = InMemoryGraphStore(
        expand_per_term_limit=2,
        direct_hit_weight=1.0,
        expanded_hit_weight=0.5,
        max_expanded_terms=10,
    )

    records = [
        ChunkGraphRecord(
            chunk_id="c1",
            doc_id="d1",
            text="privacy encryption",
        ),
        ChunkGraphRecord(
            chunk_id="c2",
            doc_id="d1",
            text="encryption ciphertext",
        ),
    ]
    store.upsert_chunk_graphs(records)

    results = store.search("privacy", top_k=10)

    chunk_ids = [x.chunk_id for x in results]
    assert "c1" in chunk_ids
    assert "c2" in chunk_ids


def test_search_scores_direct_hits_higher_than_expanded_hits():
    # 测试：扩展term能召回expanded hit
    store = InMemoryGraphStore(
        expand_per_term_limit=2,
        direct_hit_weight=1.0,
        expanded_hit_weight=0.5,
        max_expanded_terms=10,
    )

    records = [
        ChunkGraphRecord(chunk_id="c1", doc_id="d1", text="privacy encryption"),
        ChunkGraphRecord(chunk_id="c2", doc_id="d1", text="encryption ciphertext"),
    ]
    store.upsert_chunk_graphs(records)

    results = store.search("privacy", top_k=10)

    assert results[0].chunk_id == "c1"
    assert results[0].score >= results[1].score



def test_search_uses_stable_order_when_scores_tie():
    # 测试: 同分稳定排序
    store = InMemoryGraphStore()

    records = [
        ChunkGraphRecord(chunk_id="c1", doc_id="d1", text="alpha"),
        ChunkGraphRecord(chunk_id="c2", doc_id="d1", text="alpha"),
    ]
    store.upsert_chunk_graphs(records)

    results = store.search("alpha", top_k=10)

    assert [x.chunk_id for x in results] == ["c1", "c2"]
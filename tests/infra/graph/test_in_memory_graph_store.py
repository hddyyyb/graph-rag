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
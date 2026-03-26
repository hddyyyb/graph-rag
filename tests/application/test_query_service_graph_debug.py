from graph_rag.application.query_option import QueryOptions
from graph_rag.domain.graph_models import ChunkGraphRecord
from graph_rag.infra.adapters import InMemoryGraphStore
from tests.helpers import build_test_service


def test_query_service_attaches_graph_debug():
    graph_store = InMemoryGraphStore(
        expand_per_term_limit=2,
        direct_hit_weight=1.0,
        expanded_hit_weight=0.5,
    )
    graph_store.upsert_chunk_graphs([
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

    service = build_test_service(graph_store=graph_store)

    response = service.query(
        query="python",
        options=QueryOptions(enable_vector=False, enable_graph=True, top_k=5),
    )

    graph_debug = response.retrieval_debug["graph"]

    assert "graph" in response.retrieval_debug
    assert graph_debug is not None
    assert "direct_terms" in graph_debug
    assert "expanded_terms" in graph_debug
    assert "chunks" in graph_debug
    assert isinstance(graph_debug["direct_terms"], list)
    assert isinstance(graph_debug["expanded_terms"], list)
    assert isinstance(graph_debug["chunks"], list)
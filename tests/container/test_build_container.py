from graph_rag.api.main import build_container
from graph_rag.infra.config.settings import Settings


# 测试1：memory/memory 组合 wiring 正确
def test_build_container_memory_memory_wiring():
    settings = Settings(
        vector_store_backend="memory",
        graph_store_backend="memory",
        llm_backend="fake",
    )
    container = build_container(settings)

    assert container["vector_store"].__class__.__name__ == "InMemoryVectorStore"
    assert container["graph_store"].__class__.__name__ == "InMemoryGraphStore"


# 测试2：sqlite/memory 组合 wiring 正确
def test_build_container_sqlite_memory_wiring(tmp_path):
    settings = Settings(
        vector_store_backend="sqlite",
        sqlite_path=str(tmp_path / "test.db"),
        graph_store_backend="memory",
        llm_backend="fake",
    )
    container = build_container(settings)

    assert container["vector_store"].__class__.__name__ == "SQLiteVectorStore"
    assert container["graph_store"].__class__.__name__ == "InMemoryGraphStore"


# 测试3：ingest/query 共用同一 vector_store
def test_container_shares_same_vector_store_instance(tmp_path):
    settings = Settings(
        vector_store_backend="sqlite",
        sqlite_path=str(tmp_path / "shared.db"),
        graph_store_backend="memory",
        llm_backend="fake",
    )
    container = build_container(settings)

    vector_store = container["vector_store"]
    ingest_service = container["ingest_service"]
    query_service = container["query_service"]

    assert ingest_service.vector_store is vector_store
    assert query_service.vector_store is vector_store


# 测试4：ingest/query 共用同一 graph_store
def test_container_shares_same_graph_store_instance():
    settings = Settings(
        vector_store_backend="memory",
        graph_store_backend="memory",
        llm_backend="fake",
    )
    container = build_container(settings)

    graph_store = container["graph_store"]
    ingest_service = container["ingest_service"]
    query_service = container["query_service"]

    assert ingest_service.graph_store is graph_store
    assert query_service.graph_store is graph_store


def test_build_container_passes_graph_retrieval_v2_settings_to_memory_store():
    settings = Settings(
        graph_store_backend="memory",
        graph_expand_per_term_limit=3,
        graph_direct_hit_weight=1.0,
        graph_expanded_hit_weight=0.25,
        graph_max_expanded_terms=7,
    )

    container = build_container(settings)
    graph_store = container["graph_store"]

    assert graph_store.expand_per_term_limit == 3
    assert graph_store.direct_hit_weight == 1.0
    assert graph_store.expanded_hit_weight == 0.25
    assert graph_store.max_expanded_terms == 7




def test_build_container_passes_graph_weighted_config_to_memory_store():
    settings = Settings(
        graph_store_backend="memory",
        graph_expand_per_term_limit=3,
        graph_max_expanded_terms=7,
        graph_direct_hit_weight=1.2,
        graph_expanded_hit_weight=0.4,
    )

    container = build_container(settings)
    graph_store = container["graph_store"]

    assert graph_store.expand_per_term_limit == 3
    assert graph_store.max_expanded_terms == 7
    assert graph_store.direct_hit_weight == 1.2
    assert graph_store.expanded_hit_weight == 0.4
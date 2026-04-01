from graph_rag.infra.config import Settings
import pytest


# 测试1：backend selector 会被 normalize
def test_settings_normalize_backend_names():
    settings = Settings(
        vector_store_backend="SQLite",
        graph_store_backend="Neo4J",
        llm_backend="FAKE",
    )
    assert settings.vector_store_backend == "sqlite"
    assert settings.graph_store_backend == "neo4j"
    assert settings.llm_backend == "fake"


# 测试2：sqlite 缺 path 报错
def test_settings_sqlite_uses_default_memory_path():
    settings = Settings(vector_store_backend="sqlite")
    assert settings.vector_store_backend == "sqlite"
    assert settings.sqlite_path == ":memory:"

def test_settings_sqlite_empty_path_raises():
    with pytest.raises(ValueError):
        Settings(vector_store_backend="sqlite", sqlite_path="")


# 测试3：neo4j 缺连接信息报错
def test_settings_neo4j_uses_default_connection_fields():
    settings = Settings(graph_store_backend="neo4j")
    assert settings.graph_store_backend == "neo4j"
    assert settings.neo4j_uri == "bolt://localhost:7687"
    assert settings.neo4j_username == "neo4j"
    assert settings.neo4j_password == "00000000"
    assert settings.neo4j_database == "neo4j"

def test_settings_neo4j_empty_username_raises():
    with pytest.raises(ValueError):
        Settings(
            graph_store_backend="neo4j",
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="",
            neo4j_password="00000000",
        )


# 测试4：chunk overlap 非法时报错
def test_settings_chunk_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        Settings(chunk_size=100, chunk_overlap=100)


# 测试5：非法 backend 值报错
def test_settings_invalid_vector_backend_raises():
    with pytest.raises(ValueError):
        Settings(vector_store_backend="abc")


def test_settings_graph_retrieval_v2_defaults():
    settings = Settings()

    assert settings.graph_expand_per_term_limit == 2
    assert settings.graph_direct_hit_weight == 1.0
    assert settings.graph_expanded_hit_weight == 0.5
    assert settings.graph_max_expanded_terms == 10


def test_settings_rejects_expanded_weight_greater_than_direct_weight():
    with pytest.raises(ValueError):
        Settings(
            graph_direct_hit_weight=0.5,
            graph_expanded_hit_weight=1.0,
        )



def test_settings_graph_weighted_defaults():
    settings = Settings()

    assert settings.graph_expand_per_term_limit == 2
    assert settings.graph_max_expanded_terms == 10
    assert settings.graph_direct_hit_weight == 1.0
    assert settings.graph_expanded_hit_weight == 0.5
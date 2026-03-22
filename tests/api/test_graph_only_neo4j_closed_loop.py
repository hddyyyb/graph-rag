from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from neo4j import GraphDatabase

from graph_rag.api.main import create_app

from dotenv import load_dotenv

load_dotenv()

def _require_neo4j_env() -> tuple[str, str, str, str | None]:
    """
    Read Neo4j test connection info from environment variables.

    Expected env vars:
    - NEO4J_URI
    - NEO4J_USERNAME
    - NEO4J_PASSWORD
    Optional:
    - NEO4J_DATABASE

    If required vars are missing, the test module will be skipped.
    """
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE")

    if not uri or not username or not password:
        pytest.skip(
            "Neo4j test env is not configured. "
            "Please set NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD."
        )

    return uri, username, password, database


@pytest.fixture
def neo4j_config():
    uri, username, password, database = _require_neo4j_env()
    return {
        "neo4j_uri": uri,
        "neo4j_username": username,
        "neo4j_password": password,
        "neo4j_database": database,
    }


@pytest.fixture
def neo4j_driver(neo4j_config):
    driver = GraphDatabase.driver(
        neo4j_config["neo4j_uri"],
        auth=(neo4j_config["neo4j_username"], neo4j_config["neo4j_password"]),
    )
    try:
        yield driver
    finally:
        driver.close()


def _wipe_all_nodes(driver, database: str | None) -> None:
    with driver.session(database=database) as session:
        session.run("MATCH (n) DETACH DELETE n")


@pytest.fixture
def clean_graph(neo4j_driver, neo4j_config):
    _wipe_all_nodes(neo4j_driver, neo4j_config["neo4j_database"])
    try:
        yield
    finally:
        _wipe_all_nodes(neo4j_driver, neo4j_config["neo4j_database"])


@pytest.mark.integration
def test_create_app_uses_neo4j_graph_store(neo4j_config, clean_graph):
    app = create_app(
        settings_override={
            "graph_store_backend": "neo4j",
            "vector_store_backend": "memory",
            "neo4j_uri": neo4j_config["neo4j_uri"],
            "neo4j_username": neo4j_config["neo4j_username"],
            "neo4j_password": neo4j_config["neo4j_password"],
            "neo4j_database": neo4j_config["neo4j_database"],
        }
    )

    graph_store = app.state.container["graph_store"]
    assert graph_store.__class__.__name__ == "Neo4jGraphStore"


@pytest.mark.integration
def test_graph_only_closed_loop_with_neo4j(neo4j_config, clean_graph):
    app = create_app(
        settings_override={
            "graph_store_backend": "neo4j",
            "vector_store_backend": "memory",
            "neo4j_uri": neo4j_config["neo4j_uri"],
            "neo4j_username": neo4j_config["neo4j_username"],
            "neo4j_password": neo4j_config["neo4j_password"],
            "neo4j_database": neo4j_config["neo4j_database"],
        }
    )

    with TestClient(app) as client:
        ingest_resp = client.post(
            "/ingest",
            json={
                "doc_id": "doc_neo4j_graph_only_1",
                "text": "Neo4j supports graph retrieval with chunk term indexing.",
                "metadata": {},
            },
        )
        assert ingest_resp.status_code == 200, ingest_resp.text

        ingest_body = ingest_resp.json()
        assert ingest_body["doc_id"] == "doc_neo4j_graph_only_1"
        assert "trace_id" in ingest_body
        assert ingest_body["trace_id"]

        query_resp = client.post(
            "/query",
            json={
                "query": "graph retrieval",
                "top_k": 3,
                "enable_graph": True,
                "enable_vector": False,
            },
        )
        assert query_resp.status_code == 200, query_resp.text

        body = query_resp.json()

        assert "answer" in body
        assert "trace_id" in body
        assert "retrieval_debug" in body
        assert "citations" in body

        assert body["trace_id"]
        assert body["retrieval_debug"] is not None

        # 这里不强依赖 answer 的具体文本内容，
        # 因为 answer 可能受 kernel / fake llm 实现影响。
        # 重点是 graph-only 路径能走通并返回正常结构。
        assert isinstance(body["citations"], list)


@pytest.mark.integration
def test_graph_only_query_can_hit_neo4j_storage_directly(
    neo4j_config,
    neo4j_driver,
    clean_graph,
):
    app = create_app(
        settings_override={
            "graph_store_backend": "neo4j",
            "vector_store_backend": "memory",
            "neo4j_uri": neo4j_config["neo4j_uri"],
            "neo4j_username": neo4j_config["neo4j_username"],
            "neo4j_password": neo4j_config["neo4j_password"],
            "neo4j_database": neo4j_config["neo4j_database"],
        }
    )

    with TestClient(app) as client:
        ingest_resp = client.post(
            "/ingest",
            json={
                "doc_id": "doc_neo4j_graph_only_2",
                "text": "Cypher and Neo4j are useful for graph retrieval experiments.",
                "metadata": {},
            },
        )
        assert ingest_resp.status_code == 200, ingest_resp.text

        # 直接检查Neo4j里确实落了Chunk/Term关系
        with neo4j_driver.session(database=neo4j_config["neo4j_database"]) as session:
            row = session.run(
                """
                MATCH (c:Chunk)-[:MENTIONS]->(t:Term)
                WHERE c.doc_id = $doc_id AND t.name IN ["neo4j", "graph", "retrieval"]
                RETURN count(*) AS cnt
                """,
                doc_id="doc_neo4j_graph_only_2",
            ).single()

        assert row is not None
        assert row["cnt"] >= 1

        query_resp = client.post(
            "/query",
            json={
                "query": "neo4j graph",
                "top_k": 3,
                "enable_graph": True,
                "enable_vector": False,
            },
        )
        assert query_resp.status_code == 200, query_resp.text

        body = query_resp.json()
        assert body["trace_id"]
        assert isinstance(body["citations"], list)
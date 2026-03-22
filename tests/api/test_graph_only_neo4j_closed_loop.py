from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from neo4j import GraphDatabase

from graph_rag.api.main import create_app

from dotenv import load_dotenv

load_dotenv()



"""
API-level integration tests.

These tests validate the end-to-end system behavior through FastAPI:
- application initialization via create_app()
- document ingestion via /ingest
- query execution via /query

The goal is to ensure the full GraphRAG pipeline works correctly when
Neo4j is used as the graph backend.
"""




# -----------------------------------------------------------------------------
# environment helpers
# -----------------------------------------------------------------------------

def _require_neo4j_env() -> tuple[str, str, str, str | None]:
    """
    Read Neo4j connection info from environment variables.

    Required:
    - NEO4J_URI
    - NEO4J_USERNAME
    - NEO4J_PASSWORD

    Optional:
    - NEO4J_DATABASE

    If required variables are missing, the tests will be skipped.
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


# -----------------------------------------------------------------------------
# fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def neo4j_config(): 
    """
    Provide Neo4j connection settings as a dictionary.
    """
    uri, username, password, database = _require_neo4j_env()
    return {
        "neo4j_uri": uri,
        "neo4j_username": username,
        "neo4j_password": password,
        "neo4j_database": database,
    }


@pytest.fixture
def neo4j_driver(neo4j_config):
    """
    Provide a real Neo4j driver instance.

    The driver is automatically closed after the test.
    """
    driver = GraphDatabase.driver(
        neo4j_config["neo4j_uri"],
        auth=(neo4j_config["neo4j_username"], neo4j_config["neo4j_password"]),
    )
    try:
        yield driver  
    finally:
        driver.close()
    # yield = “返回一个值，但函数不会结束，下次还能从这里继续执行”

#  pytest 在同一个 scope 生命周期内会缓存 fixture 的结果

# -----------------------------------------------------------------------------
# graph cleanup
# -----------------------------------------------------------------------------

def _wipe_all_nodes(driver, database: str | None) -> None:
    """
    Remove all nodes and relationships from the test database.

    This ensures test isolation across runs.
    """
    with driver.session(database=database) as session:  # ① 打开一个 session:“我现在要操作 Neo4j 这个数据库了”
        session.run("MATCH (n) DETACH DELETE n")  # ② 执行 Cypher
        # MATCH (n) 找到所有节点
        # DETACH DELETE n 删除这些节点和它们的关系


@pytest.fixture
def clean_graph(neo4j_driver, neo4j_config):  # 得到yield driver, 和neo4j_config返回值
    _wipe_all_nodes(neo4j_driver, neo4j_config["neo4j_database"])  # Step 1：测试开始前
    try:
        yield    # Step 2：进入测试
    finally:    # Step 4：测试结束后
        _wipe_all_nodes(neo4j_driver, neo4j_config["neo4j_database"])



# -----------------------------------------------------------------------------
# tests
# -----------------------------------------------------------------------------

# @标记是集成测试
# 可以只跑集成测试 pytest -m integration
@pytest.mark.integration
def test_create_app_uses_neo4j_graph_store(neo4j_config, clean_graph):
    """
    Verify that the application correctly wires Neo4jGraphStore when
    graph_store_backend is set to "neo4j".
    """
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
    # graph_store.__class__ 表示 这个对象的“类”，
    # graph_store.__class__.__name__ 表示：这个类的名字（字符串）


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

    # 从API层发起一次真实文档写入，再发起一次只走图检索的查询，整条流程能不能闭环跑通
    with TestClient(app) as client:  # 用TestClient(app)模拟HTTP请求
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
        # 这段Cypher的意思是：
        # 找到Chunk节点
        # 找到它通过MENTIONS关系连接到的Term节点
        # 只看当前这个doc_id 
        # 并且Term名字是neo4j / graph / retrieval之一 
        # 最后统计这样的关系有多少条
        
        assert row is not None
        assert row["cnt"] >= 1

        # 至少有一条Chunk -> Term关系，真的被写进了Neo4j。

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
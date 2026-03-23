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
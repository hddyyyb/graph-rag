from __future__ import annotations

from fastapi.testclient import TestClient

from graph_rag.api.main import create_app


def test_smoke_health_ingest_query():
    app = create_app()
    client = TestClient(app)

    # health
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # ingest
    ingest_payload = {
        "doc_id": "doc1",
        "text": "GraphRAG系统包含向量检索与图检索两条通道。Neo4j用于图存储，Milvus用于向量存储。",
        "metadata": {"source": "unit_test"},
    }
    r = client.post("/ingest", json=ingest_payload)
    assert r.status_code == 200
    body = r.json()
    assert body["doc_id"] == "doc1"
    assert body["chunks"] >= 1
    assert body["trace_id"]
    assert r.headers.get("x-trace-id")  # middleware写回

    # query
    query_payload = {
        "query": "GraphRAG使用什么存储？",
        "top_k": 5,
        "enable_graph": True,
        "enable_vector": True,
    }
    r = client.post("/query", json=query_payload, headers={"x-trace-id": "trace_test_123"})
    assert r.status_code == 200
    body = r.json()
    assert body["trace_id"] == "trace_test_123"
    assert "retrieval_debug" in body
    assert "vector" in body["retrieval_debug"]
    assert "graph" in body["retrieval_debug"]
    assert isinstance(body.get("answer"), str)
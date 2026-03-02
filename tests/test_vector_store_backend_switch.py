from __future__ import annotations 


from fastapi.testclient import TestClient
from graph_rag.api.main import create_app


def test_vector_store_backend_switch(tmp_path):
    app = create_app(settings_override={
        "vector_store_backend": "sqlite",
        "sqlite_path": str(tmp_path / "test.db")
    })

    client = TestClient(app)

    payload = {"doc_id": "123456789", "text":"666big bomb" , "metadata": None}
    r = client.post('/ingest',json = payload)
    
    payload = {"query": "check sth", "top_k":2 , "enable_graph": True, "enable_vector": True}
    r2 = client.post('/query',json = payload)

    vector_store = app.state.container["vector_store"]
    assert type(vector_store).__name__ == "SQLiteVectorStore"
    

    app2 = create_app(settings_override={
        "vector_store_backend": "memory"
    })
    client2 = TestClient(app2)
    
    payload = {"doc_id": "123456789", "text":"666big bomb" , "metadata": None}
    r3 = client2.post('/ingest',json = payload)
    
    payload = {"query": "check sth", "top_k":2 , "enable_graph": True, "enable_vector": True}
    r4 = client2.post('/query',json = payload)

    vector_store = app2.state.container["vector_store"]
    assert type(vector_store).__name__ == "InMemoryVectorStore"
    
    

def test_vector_store_backend_switch2(tmp_path):
    # sqlite实现持久化（重启还在）

    settings_override={
        "vector_store_backend": "sqlite",
        "sqlite_path": str(tmp_path / "test.db")
    }
    app = create_app(settings_override=settings_override)

    client = TestClient(app)

    payload = {"doc_id": "123456789", "text":"666big bomb" , "metadata": None}
    r = client.post('/ingest',json = payload)
    

    app_reboot = create_app(settings_override=settings_override)
    client_reboot = TestClient(app_reboot)
    
    
    payload2 = {"query": "check sth", "top_k":2 , "enable_graph": True, "enable_vector": True}
    r4 = client_reboot.post('/query',json = payload2)

    dbg = r4.json()["retrieval_debug"]
    assert dbg["merged"]["count"] > 0
    #print(r4.json()["retrieval_debug"])


def test_memory_backend_not_persistent(tmp_path):
    # 新增Test3：Memory不持久化（对照组）
    settings_override = {"vector_store_backend": "memory"}

    app = create_app(settings_override=settings_override)
    client = TestClient(app)

    client.post("/ingest", json={"doc_id": "d1", "text": "666big bomb", "metadata": None})

    app2 = create_app(settings_override=settings_override)
    client2 = TestClient(app2)

    r = client2.post("/query", json={"query": "check sth", "top_k": 2, "enable_graph": True, "enable_vector": True})

    dbg = r.json()["retrieval_debug"]
    assert dbg["merged"]["count"] == 0
    # 或者 assert len(dbg["vector"]["hits"]) == 0
    
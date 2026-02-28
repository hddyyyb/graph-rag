from __future__ import annotations

from fastapi.testclient import TestClient

from graph_rag.api.main import create_app


def test_embedding_pluggable():
    app = create_app()
    client = TestClient(app)

    ingest_payload = {"doc_id":"doc777","text":"a simple Try","metadata":{"source":"unit_test"}}
    client.post("/ingest", json= ingest_payload)

    vs = app.state.container["vector_store"]

    target_doc = "doc777"
    found = 0
    #key: (doc_id, chunk_id) -> (text, embedding)
    for (doc_id, chunk_id),(txt, emb) in vs._data.items():
        if doc_id != target_doc:
            continue
        found += 1
        assert emb[0] == 999

    assert found > 0


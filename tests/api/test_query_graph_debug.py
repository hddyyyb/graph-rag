


def test_query_api_returns_graph_debug(client):
    payload = {
        "doc_id": "doc1",
        "text": "python fastapi tutorial. django backend framework."
    }
    ingest_resp = client.post("/ingest", json=payload)
    assert ingest_resp.status_code == 200

    query_resp = client.post(
        "/query",
        json={
            "query": "python",
            "top_k": 5,
            "enable_vector": False,
            "enable_graph": True,
        },
    )
    assert query_resp.status_code == 200

    body = query_resp.json()
    assert "retrieval_debug" in body
    assert "graph" in body["retrieval_debug"]

    graph_debug = body["retrieval_debug"]["graph"]
    assert graph_debug is not None
    assert "query" in graph_debug
    assert "direct_terms" in graph_debug
    assert "expanded_terms" in graph_debug
    assert "chunks" in graph_debug

    assert graph_debug["query"] == "python"
    assert isinstance(graph_debug["direct_terms"], list)
    assert isinstance(graph_debug["expanded_terms"], list)
    assert isinstance(graph_debug["chunks"], list)

    assert len(graph_debug["chunks"]) >= 1
    first = graph_debug["chunks"][0]
    assert "chunk_id" in first
    assert "doc_id" in first
    assert "direct_hit_count" in first
    assert "expanded_hit_count" in first
    assert "score" in first
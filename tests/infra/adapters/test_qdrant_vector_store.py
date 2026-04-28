import pytest

from graph_rag.infra.adapters.qdrant_vector_store import QdrantVectorStore


@pytest.mark.integration
def test_qdrant_upsert_and_search_with_docker():
    store = QdrantVectorStore(
        host="localhost",
        port=6334,
        collection_name="test_graphrag_qdrant",
    )

    store.upsert(
        doc_id="d1",
        chunk_ids=["c1", "c2"],
        chunks=["hello world", "foo bar"],
        embeddings=[
            [1.0, 0.0],
            [0.0, 1.0],
        ],
    )

    results = store.search(
        query_embedding=[1.0, 0.0],
        top_k=2,
    )

    assert len(results) > 0
    assert results[0].chunk_id == "c1"
    assert results[0].doc_id == "d1"
    assert results[0].text == "hello world"
    assert results[0].source == "qdrant"
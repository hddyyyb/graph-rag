from graph_rag.infra.adapters import InMemoryVectorStore
from graph_rag.infra.adapters import SQLiteVectorStore


def test_inmemory_search_filter_doc_id():
    store = InMemoryVectorStore()

    store.upsert("doc1", ["a", "b"], [[1.0, 0.0], [0.8, 0.2]])
    store.upsert("doc2", ["c", "d"], [[0.0, 1.0], [0.2, 0.8]])

    hits_all = store.search([1.0, 0.0], top_k=10)
    assert len(hits_all) > 0

    hits_doc1 = store.search([1.0, 0.0], top_k=10, filter_doc_id="doc1")
    assert len(hits_doc1) > 0
    assert all(h.doc_id == "doc1" for h in hits_doc1)

    hits_doc2 = store.search([1.0, 0.0], top_k=10, filter_doc_id="doc2")
    assert len(hits_doc2) > 0
    assert all(h.doc_id == "doc2" for h in hits_doc2)

def test_sqlite_search_filter_doc_id(tmp_path):
    db_path = str(tmp_path / "day5.db")
    store = SQLiteVectorStore(db_path)

    store.upsert("doc1", ["a", "b"], [[1.0, 0.0], [0.8, 0.2]])
    store.upsert("doc2", ["c", "d"], [[0.0, 1.0], [0.2, 0.8]])

    hits_doc1 = store.search([1.0, 0.0], top_k=10, filter_doc_id="doc1")
    assert len(hits_doc1) > 0
    assert all(h.doc_id == "doc1" for h in hits_doc1)

    hits_doc2 = store.search([1.0, 0.0], top_k=10, filter_doc_id="doc2")
    assert len(hits_doc2) > 0
    assert all(h.doc_id == "doc2" for h in hits_doc2)
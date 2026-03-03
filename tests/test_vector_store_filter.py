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



def test_inmemory_search_filter_min_score():
    store = InMemoryVectorStore()

    # doc1里两条：与query=[1,0]的相似度分别是 1.0 和 0.8（假设你们是点积或cos且向量已近似单位化）
    store.upsert("doc1", ["a", "b"], [[1.0, 0.0], [0.8, 0.2]])
    # doc2里两条：与query=[1,0]的相似度分别是 0.0 和 0.2
    store.upsert("doc2", ["c", "d"], [[0.0, 1.0], [0.2, 0.8]])

    # 默认行为：不过滤（等价于 min_score=None）
    hits_default = store.search([1.0, 0.0], top_k=10)
    assert len(hits_default) > 0

    # 阈值=0.8：只保留 score>=0.8 的结果（预计只剩 doc1 的两条或至少包含它们）
    hits_min_08 = store.search([1.0, 0.0], top_k=10, min_score=0.8)
    assert len(hits_min_08) > 0
    assert all(h.score >= 0.8 for h in hits_min_08)

    # 阈值=0.9：预计只剩下最相似的那条（score=1.0）
    hits_min_09 = store.search([1.0, 0.0], top_k=10, min_score=0.9)
    assert len(hits_min_09) > 0
    assert all(h.score >= 0.9 for h in hits_min_09)

    # 阈值>1.0：应该为空
    hits_min_11 = store.search([1.0, 0.0], top_k=10, min_score=1.1)
    assert hits_min_11 == []

    # 这是“默认行为锁定测试”，
    # 未来别人改代码时，如果破坏默认行为会立刻爆红。
    hits_none = store.search([1.0, 0.0], top_k=10, min_score=None)
    assert hits_none == hits_default


def test_sqlite_search_filter_min_score(tmp_path):
    db_path = tmp_path / "chunks.db"
    store = SQLiteVectorStore(str(db_path))  # 如果你构造函数不是这样，改成你项目的写法

    store.upsert("doc1", ["a", "b"], [[1.0, 0.0], [0.8, 0.2]])
    store.upsert("doc2", ["c", "d"], [[0.0, 1.0], [0.2, 0.8]])

    hits_default = store.search([1.0, 0.0], top_k=10)
    assert len(hits_default) > 0

    hits_min_08 = store.search([1.0, 0.0], top_k=10, min_score=0.8)
    assert len(hits_min_08) > 0
    assert all(h.score >= 0.8 for h in hits_min_08)

    hits_min_11 = store.search([1.0, 0.0], top_k=10, min_score=1.1)
    assert hits_min_11 == []
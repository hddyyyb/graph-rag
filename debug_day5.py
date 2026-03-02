from graph_rag.infra.adapters.milvus_store import InMemoryVectorStore

from typing import List



def main() -> None:
    store = InMemoryVectorStore()

    # 1) 准备两份doc的数据
    doc1_chunks: List[str] = ["doc1 chunk A", "doc1 chunk B"]
    doc2_chunks: List[str] = ["doc2 chunk A", "doc2 chunk B"]

    # 2) 准备embedding（维度保持一致即可）
    # 让query=[1,0]更接近doc1，doc2相对不接近，方便观察
    doc1_embs: List[List[float]] = [[1.0, 0.0], [0.8, 0.2]]
    doc2_embs: List[List[float]] = [[0.0, 1.0], [0.2, 0.8]]

    # 3) upsert写入（符合你的接口：doc_id + chunks + embeddings）
    store.upsert(doc_id="doc1", chunks=doc1_chunks, embeddings=doc1_embs)
    store.upsert(doc_id="doc2", chunks=doc2_chunks, embeddings=doc2_embs)

    query_embedding: List[float] = [1.0, 0.0]

    # 4) 不过滤：应该能看到doc1和doc2都有结果（top_k足够大）
    print("=== no filter ===")
    hits = store.search(query_embedding=query_embedding, top_k=10)
    for h in hits:
        print(h.doc_id, h.chunk_id, round(h.score, 4))

    # 5) 过滤doc1：结果里只能出现doc1
    print("=== filter doc1 ===")
    hits = store.search(query_embedding=query_embedding, top_k=10, filter_doc_id="doc1")
    for h in hits:
        print(h.doc_id, h.chunk_id, round(h.score, 4))
    assert all(h.doc_id == "doc1" for h in hits), "filter_doc_id=doc1 should only return doc1 chunks"

    # 6) 过滤doc2：结果里只能出现doc2
    print("=== filter doc2 ===")
    hits = store.search(query_embedding=query_embedding, top_k=10, filter_doc_id="doc2")
    for h in hits:
        print(h.doc_id, h.chunk_id, round(h.score, 4))
    assert all(h.doc_id == "doc2" for h in hits), "filter_doc_id=doc2 should only return doc2 chunks"

    print("OK ✅ filter_doc_id works for InMemoryVectorStore")


if __name__ == "__main__":
    main()
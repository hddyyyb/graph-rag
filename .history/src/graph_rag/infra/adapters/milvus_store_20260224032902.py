from __future__ import annotations

import math
from typing import Dict, List, Tuple

from graph_rag.domain.models import RetrievedChunk
from graph_rag.ports.vector_store import VectorStorePort


'''
InMemoryVectorStore保存(doc_id, chunk_id) -> (text, embedding)
search()用cosine相似度做top_k检索
目的：先把“向量写入+向量检索”链路跑通
Day3换成真正Milvus适配器。
'''
def _cosine(a: List[float], b: List[float]) -> float:
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    denom = math.sqrt(na) * math.sqrt(nb)
    if denom == 0:
        return 0.0
    return dot / denom


class InMemoryVectorStore(VectorStorePort):
    """
    Day2代替Milvus的内存向量库，接口保持一致，便于Day3替换。
    """

    def __init__(self) -> None:
        # key: (doc_id, chunk_id) -> (text, embedding)
        self._data: Dict[Tuple[str, str], Tuple[str, List[float]]] = {}

    def upsert(self, doc_id: str, chunks: List[str], embeddings: List[List[float]]) -> None:
        for idx, (txt, emb) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"c{idx}"
            self._data[(doc_id, chunk_id)] = (txt, emb)

    def search(self, query_embedding: List[float], top_k: int) -> List[RetrievedChunk]:
        scored: List[Tuple[float, Tuple[str, str], str]] = []
        for (doc_id, chunk_id), (txt, emb) in self._data.items():
            score = _cosine(query_embedding, emb)
            scored.append((score, (doc_id, chunk_id), txt))
        scored.sort(key=lambda x: x[0], reverse=True)

        out: List[RetrievedChunk] = []
        for score, (doc_id, chunk_id), txt in scored[: max(top_k, 0)]:
            out.append(
                RetrievedChunk(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    text=txt,
                    score=float(score),
                    source="vector",
                )
            )
        return out
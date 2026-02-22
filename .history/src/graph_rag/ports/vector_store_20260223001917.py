from __future__ import annotations

from typing import List, Protocol

from graph_rag.domain.models import RetrievedChunk


# Application层想用向量检索，它需要什么方法？
# 必须支持写入（upsert）
# 必须支持检索（search）
# Infra层必须把底层数据转换成Domain对象再返回。

class VectorStorePort(Protocol):
    def upsert(self, doc_id: str, chunks: List[str], embeddings: List[List[float]]) -> None:
        ...

    def search(self, query_embedding: List[float], top_k: int) -> List[RetrievedChunk]:
        ...
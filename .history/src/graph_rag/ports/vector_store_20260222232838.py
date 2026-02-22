from __future__ import annotations

from typing import List, Protocol

from graph_rag.domain.models import RetrievedChunk


class VectorStorePort(Protocol):
    def upsert(self, doc_id: str, chunks: List[str], embeddings: List[List[float]]) -> None:
        ...

    def search(self, query_embedding: List[float], top_k: int) -> List[RetrievedChunk]:
        ...
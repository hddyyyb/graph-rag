from __future__ import annotations

from typing import List, Protocol

from graph_rag.domain.models import RetrievedChunk


class GraphStorePort(Protocol):
    def upsert_document(self, doc_id: str, chunks: List[str]) -> None:
        ...

    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        ...
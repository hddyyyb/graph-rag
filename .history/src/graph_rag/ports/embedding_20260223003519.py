from __future__ import annotations

from typing import List, Protocol


class EmbeddingProviderPort(Protocol):
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        ...

    def embed_query(self, query: str) -> List[float]:
        ...
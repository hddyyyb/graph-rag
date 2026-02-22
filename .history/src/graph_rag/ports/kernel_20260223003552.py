from __future__ import annotations

from typing import List, Protocol

from graph_rag.domain.models import RetrievedChunk


class RAGKernelPort(Protocol):
    def generate_answer(self, query: str, contexts: List[RetrievedChunk]) -> str:
        ...
from __future__ import annotations

from typing import List

from graph_rag.ports.kernel import RAGKernelPort
from graph_rag.domain.models import RetrievedChunk

class FakeKernel(RAGKernelPort):
    def __init__(self) -> None:
        self.last_query = ""
        self.last_chunks = []
        self.reply = "fake-answer"

    def generate_answer(self, query: str, contexts: List[RetrievedChunk]):
        self.last_query = query
        self.last_chunks = contexts
        return self.reply
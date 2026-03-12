from __future__ import annotations

from graph_rag.ports.kernel import RAGKernelPort

class FakeKernel(RAGKernelPort):
    def __init__(self) -> None:
        self.last_query = ""
        self.last_chunks = []
        self.reply = "fake-answer"

    def generate_answer(self, query: str, chunks):
        self.last_query = query
        self.last_chunks = chunks
        return self.reply
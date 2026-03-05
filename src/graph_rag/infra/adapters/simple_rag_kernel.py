# src\graph_rag\infra\adapters\simple_rag_kernel.py
from __future__ import annotations

from typing import List

from graph_rag.domain.models import RetrievedChunk  #  RetrievedChunk-GraphRAG的核心对象：它代表“一条检索到的片段”。vector_store.search返回的就是这个。
from graph_rag.ports.kernel import RAGKernelPort
from graph_rag.ports.llm import LLMPort



'''
@dataclass(frozen=True)
class RetrievedChunk:    # VectorStore返回RetrievedChunk,GraphRAG的核心对象：它代表“一条检索到的片段”。vector_store.search返回的就是这个。
    doc_id: str
    chunk_id: str
    text: str
    score: float
    source: str  # "vector" | "graph"
'''
class SimpleRAGKernel(RAGKernelPort):
    def __init__(self, llm: LLMPort):
        self.llm = llm

    def generate_answer(self, query: str, contexts: List[RetrievedChunk]) -> str:
        context_text = "\n\n".join(
            f"[{c.doc_id}:{c.chunk_id}|{c.source}|score={c.score:.4f}]\n{c.text}"
            for c in contexts[:10]
        )
        prompt = (
            "你是一个严谨的企业级RAG助手。请仅根据给定上下文回答问题。\n\n"
            f"问题：{query}\n\n"
            "上下文：\n"
            f"{context_text}\n\n"
            "回答："
        )
        return self.llm.generate(prompt)
from __future__ import annotations

from typing import List

from graph_rag.domain.models import RetrievedChunk
from graph_rag.ports.kernel import RAGKernelPort


class SimpleKernel(RAGKernelPort):
    """
    Day2最小Kernel：把检索到的上下文拼起来，输出结构化可解释的回答。
    Day3再替换成LlamaIndex/可插拔LLM（并接prompt模板、流式输出等）。
    """

    def generate_answer(self, query: str, contexts: List[RetrievedChunk]) -> str:
        if not contexts:
            return f"未检索到相关上下文。query={query}"

        # Keep it deterministic for tests
        top = contexts[:3]
        bullets = []
        for c in top:
            snippet = c.text.replace("\n", " ").strip()
            if len(snippet) > 160:
                snippet = snippet[:160] + "..."
            bullets.append(f"- [{c.source}] {c.doc_id}/{c.chunk_id} score={c.score:.3f}: {snippet}")

        return "基于检索到的上下文，给出一个最小可用回答（Day2占位）：\n" + "\n".join(bullets)
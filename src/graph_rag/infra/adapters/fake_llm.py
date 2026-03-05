# src/graph_rag/infra/adapters/fake_llm.py
from __future__ import annotations

from dataclasses import dataclass
from graph_rag.ports.llm import LLMPort


@dataclass
class FakeLLM(LLMPort):
    reply: str = "fake-answer"
    last_prompt: str = ""

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.reply
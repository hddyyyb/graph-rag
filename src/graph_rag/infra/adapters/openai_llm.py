# src\graph_rag\infra\adapters\openai_llm.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from graph_rag.ports.llm import LLMPort


@dataclass
class OpenAILLM(LLMPort):
    api_key: Optional[str] = None
    model: str = "gpt-5"
    instructions: str = "You are a helpful assistant."

    def generate(self, prompt: str) -> str:
        # 延迟导入：避免在未安装openai时影响离线测试
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        res = client.responses.create(
            model=self.model,
            instructions=self.instructions,
            input=prompt,
        )
        # output_text is the SDK convenience field shown in official docs
        return (res.output_text or "").strip()
    
# 官方示例
# https://developers.openai.com/api/docs/guides/migrate-to-responses/?utm_source=chatgpt.com
# client.responses.create(...);
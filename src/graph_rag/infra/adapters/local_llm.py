# 标准库urllib

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict
from urllib.request import Request, urlopen

from graph_rag.ports.llm import LLMPort


@dataclass
class LocalLLM(LLMPort):
    base_url: str = "http://localhost:11434"
    model: str = "llama3"
    timeout_s: float = 60.0

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

        with urlopen(req, timeout=self.timeout_s) as resp:
            body = resp.read().decode("utf-8")
            obj = json.loads(body)

        # Ollama通常返回 {"response": "...", ...}
        return str(obj.get("response", "")).strip()
from __future__ import annotations

import hashlib
from typing import List

from graph_rag.ports.embedding import EmbeddingProviderPort


class HashEmbeddingProvider(EmbeddingProviderPort):  # 实现EmbeddingProviderPort接口
    """
    Day2最小可用Embedding：用hash生成稳定向量（不依赖外部模型）。
    Day3再替换成OpenAI/本地embedding/llama.cpp等。

    HashEmbeddingProvider把文本做hash生成固定维度向量
    目的：不依赖外部模型/网络，保证Day2闭环可跑、可测试
    Day3替换成真实embedding（OpenAI/本地模型）时，上层不用改：
    只需要改 infra层（adapters + DI容器）：

        class OpenAIEmbeddingProvider(EmbeddingProviderPort):
            def embed_texts(...):
                # 调OpenAI API
        
        修改DI容器, 在 api/main.py 里
        embedder = HashEmbeddingProvider(dim=32)
        改成
        embedder = OpenAIEmbeddingProvider(api_key=...)

    """

    def __init__(self, dim: int = 32) -> None:
        self.dim = dim

    def _hash_to_vec(self, s: str) -> List[float]:
        h = hashlib.sha256(s.encode("utf-8")).digest()
        # Expand bytes to dim floats in [0,1)
        vec: List[float] = []
        for i in range(self.dim):
            b = h[i % len(h)]
            vec.append(b / 255.0)
        return vec

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_to_vec(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self._hash_to_vec(query)
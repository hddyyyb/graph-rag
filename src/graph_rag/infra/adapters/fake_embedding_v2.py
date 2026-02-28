from graph_rag.ports.embedding import EmbeddingProviderPort
from typing import List

class FakeEmbeddingV2():
    def __init__(self, dim = 32):
        self.dim = dim

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        res = []
        for text in texts:
            emb = self._emb_one(text)
            res.append(emb)
        return res

    def embed_query(self, query: str) -> List[float]:
        return self._emb_one(query)

    def _emb_one(self, text:str) -> List[float]:
        emb = [1]* self.dim
        emb[0] = 999
        return emb


from __future__ import annotations

from typing import List

from graph_rag.ports.embedding import EmbeddingProviderPort

from sentence_transformers import SentenceTransformer

class SentenceTransformerEmbeddingProvider(EmbeddingProviderPort):

    def __init__(
            self,
            model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
            normalize_embeddings: bool = False
            ) -> None:
        self.model = SentenceTransformer(model_name)
        self.normalize_embeddings = normalize_embeddings

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=self.normalize_embeddings,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query])[0]
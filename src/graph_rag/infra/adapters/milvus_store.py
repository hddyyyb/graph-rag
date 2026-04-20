from __future__ import annotations

import math
from typing import Dict, List, Tuple, Optional

from graph_rag.domain.models import RetrievedChunk

from graph_rag.ports.vector_store import VectorStorePort, SearchOptions, normalize_search_options


def _cosine(a: List[float], b: List[float]) -> float:
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    denom = math.sqrt(na) * math.sqrt(nb)
    if denom == 0:
        return 0.0
    return dot / denom


class InMemoryVectorStore(VectorStorePort):

    def __init__(self) -> None:
        # key: (doc_id, chunk_id) -> (text, embedding)
        self._data: Dict[Tuple[str, str], Tuple[str, List[float]]] = {}

    def upsert(
        self, 
        doc_id: str, 
        chunk_ids: List[str],
        chunks: List[str], 
        embeddings: List[List[float]]
        ) -> None:
        if not (len(chunk_ids) == len(chunks) == len(embeddings)):
            raise ValueError(
                f"chunk_ids, chunks and embeddings length mismatch: "
                f"{len(chunk_ids)} != {len(chunks)} != {len(embeddings)}"
            )

        for chunk_id, txt, emb in zip(chunk_ids, chunks, embeddings):
            self._data[(doc_id, chunk_id)] = (txt, emb)

    def search(
            self, 
            query_embedding: List[float], 
            top_k: int,
            options: Optional[SearchOptions] = None,
            filter_doc_id:Optional[str] = None,
            min_score: Optional[float] = None,
            ) -> List[RetrievedChunk]:
        
        opts = normalize_search_options(
            options = options, 
            filter_doc_id = filter_doc_id,
            min_score = min_score,
            )
        scored: List[Tuple[float, Tuple[str, str], str]] = []

        # 这里是取所有 chunk 全部做匹配
        for (doc_id, chunk_id), (txt, emb) in self._data.items():
            
            if opts.filter_doc_id is not None and doc_id != opts.filter_doc_id:# 如果要过滤doc_id且不等
                continue  
            score = _cosine(query_embedding, emb)
            if opts.min_score is not None and score < opts.min_score:
                continue
            scored.append((score, (doc_id, chunk_id), txt))
        
        # 按照 score 排序
        scored.sort(key=lambda x: x[0], reverse=True)

        out: List[RetrievedChunk] = []
        for score, (doc_id, chunk_id), txt in scored[: max(top_k, 0)]:
            out.append(
                RetrievedChunk(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    text=txt,
                    score=float(score),
                    source="memory",
                )
            )
        return out
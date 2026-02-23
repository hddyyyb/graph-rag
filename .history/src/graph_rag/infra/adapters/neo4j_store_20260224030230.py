from __future__ import annotations

from typing import Dict, List

from graph_rag.domain.models import RetrievedChunk
from graph_rag.ports.graph_store import GraphStorePort


class InMemoryGraphStore(GraphStorePort):
    """
    Day2代替Neo4j：用最简单的倒排/子串匹配模拟“图检索”结果。
    Day3接Neo4j后，把search实现换成Cypher+图遍历/社区/实体扩展。
    """

    def __init__(self) -> None:
        # doc_id -> chunks
        self._docs: Dict[str, List[str]] = {}

    def upsert_document(self, doc_id: str, chunks: List[str]) -> None:
        self._docs[doc_id] = list(chunks)

    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        q = (query or "").strip().lower()
        if not q:
            return []

        hits: List[RetrievedChunk] = []
        for doc_id, chunks in self._docs.items():
            for idx, txt in enumerate(chunks):
                t = txt.lower()
                # naive match score
                score = 0.0
                if q in t:
                    score = 1.0
                else:
                    # token overlap
                    q_tokens = set(q.split())
                    t_tokens = set(t.split())
                    if q_tokens:
                        score = len(q_tokens & t_tokens) / max(len(q_tokens), 1)
                if score > 0:
                    hits.append(
                        RetrievedChunk(
                            doc_id=doc_id,
                            chunk_id=f"c{idx}",
                            text=txt,
                            score=float(score),
                            source="graph",
                        )
                    )

        hits.sort(key=lambda x: x.score, reverse=True)
        return hits[: max(top_k, 0)]
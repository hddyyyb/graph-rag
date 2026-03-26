from __future__ import annotations

from typing import Dict, Optional, List, Any

from graph_rag.domain.models import RetrievedChunk

from graph_rag.ports.graph_store import GraphStorePort



class FakeGraphStore(GraphStorePort):
    def __init__(self):
        self._last_debug: Optional[Dict[str, Any]] = None

    def upsert_chunk_graphs(self, records):
        # fake里可以忽略，或者存下来都行
        pass

    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        # 固定返回一条结果（测试用）
        chunks = [
            RetrievedChunk(
                chunk_id="c3",
                doc_id="d3",
                text="python graph rag example",
                score=0.5,
                source="graph",
            )
        ]

        # 👉 Day27 debug结构（关键）
        self._last_debug = {
            "query": query,
            "direct_terms": [query],
            "expanded_terms": [],
            "chunks": [
                {
                    "chunk_id": "c3",
                    "doc_id": "d3",
                    "score": 0.5,
                    "direct_hit_count": 0,
                    "expanded_hit_count": 1,
                }
            ],
        }

        return chunks[:top_k]

    def get_last_debug(self) -> Optional[Dict[str, Any]]:
        return self._last_debug
    
class FakeGraphStoreMinScore(GraphStorePort):
    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        r3 = RetrievedChunk(doc_id="d3", chunk_id="c3", text="graph-1", score=0.88, source="graph")
        r4 = RetrievedChunk(doc_id="d4", chunk_id="c4", text="graph-2", score=0.20, source="graph")

        return [r3, r4]

class FakeGraphStore_only_vector(GraphStorePort):
    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        return []

class FakeGraphStore_only_graph(GraphStorePort):
    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        r3 = RetrievedChunk(doc_id="d3", chunk_id="c3", text="graph-1", score=0.88, source="graph")

        return [r3]


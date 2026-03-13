from __future__ import annotations

from typing import Optional, List

from graph_rag.domain.models import RetrievedChunk

from graph_rag.ports.graph_store import GraphStorePort



class FakeGraphStore(GraphStorePort):
    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        r3 = RetrievedChunk(doc_id="d3", chunk_id="c3", text="graph-1", score=0.90, source="graph")
        return [r3]
    
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


from __future__ import annotations

from typing import Optional, List

from graph_rag.domain.models import RetrievedChunk
from graph_rag.ports.vector_store import VectorStorePort, SearchOptions



class FakeVectorStore(VectorStorePort):
    def search(
            self,
            query_embedding: List[float],
            top_k: int,
            options: Optional[SearchOptions] = None,
            filter_doc_id: Optional[str] = None,
            min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        r1 = RetrievedChunk(doc_id="d1", chunk_id="c1", text="vector-1", score=0.95, source="vector")
        r2 = RetrievedChunk(doc_id="d2", chunk_id="c2", text="vector-2", score=0.60, source="vector")
        return [r1, r2]


class FakeVectorStoreMinScore(VectorStorePort):
    def search(
            self,
            query_embedding: List[float],
            top_k: int,
            options: Optional[SearchOptions] = None,
            filter_doc_id: Optional[str] = None,
            min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        r1 = RetrievedChunk(doc_id="d1", chunk_id="c1", text="vector-1", score=0.92, source="vector")
        r2 = RetrievedChunk(doc_id="d2", chunk_id="c2", text="vector-2", score=0.30, source="vector")
        return [r1, r2]



class FakeVectorStore_only_vector(VectorStorePort):
    def search(
            self,
            query_embedding: List[float],
            top_k: int,
            options: Optional[SearchOptions] = None,
            filter_doc_id: Optional[str] = None,
            min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        r1 = RetrievedChunk(doc_id="d1", chunk_id="c1", text="vector-1", score=0.80, source="vector")
        return [r1]


class FakeVectorStore_only_graph(VectorStorePort):
    def search(
            self,
            query_embedding: List[float],
            top_k: int,
            options: Optional[SearchOptions] = None,
            filter_doc_id: Optional[str] = None,
            min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        return []
    

class FakeVectorStore12counts(VectorStorePort):
    def search(
            self,
            query_embedding: List[float],
            top_k: int,
            options: Optional[SearchOptions] = None,
            filter_doc_id: Optional[str] = None,
            min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        r1 = RetrievedChunk(doc_id="d1", chunk_id="c1", text="vector-1", score=0.92, source="vector")
        r2 = RetrievedChunk(doc_id="d2", chunk_id="c2", text="vector-2", score=0.90, source="vector")
        r3 = RetrievedChunk(doc_id="d3", chunk_id="c3", text="vector-3", score=0.92, source="vector")
        r4 = RetrievedChunk(doc_id="d4", chunk_id="c4", text="vector-4", score=0.80, source="vector")
        r5 = RetrievedChunk(doc_id="d5", chunk_id="c5", text="vector-5", score=0.72, source="vector")
        r6 = RetrievedChunk(doc_id="d6", chunk_id="c6", text="vector-6", score=0.60, source="vector")
        r7 = RetrievedChunk(doc_id="d7", chunk_id="c7", text="vector-7", score=0.92, source="vector")
        r8 = RetrievedChunk(doc_id="d8", chunk_id="c8", text="vector-8", score=0.50, source="vector")
        r9 = RetrievedChunk(doc_id="d9", chunk_id="c9", text="vector-9", score=0.95, source="vector")
        r10 = RetrievedChunk(doc_id="d10", chunk_id="c10", text="vector-10", score=0.97, source="vector")
        r11 = RetrievedChunk(doc_id="d11", chunk_id="c11", text="vector-11", score=0.99, source="vector")
        r12 = RetrievedChunk(doc_id="d12", chunk_id="c12", text="vector-12", score=0.80, source="vector")
        return [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12]




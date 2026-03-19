from __future__ import annotations

from typing import List

from graph_rag.application import IngestService
from graph_rag.domain.models import RetrievedChunk
from graph_rag.domain.graph_models import ChunkGraphRecord
from graph_rag.infra.adapters import InMemoryVectorStore
from graph_rag.infra.observability.fake_trace import FakeTrace


class FakeEmbedder:
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, query: str) -> List[float]:
        return [1.0, 0.0, 0.0]


class SpyGraphStore:
    def __init__(self) -> None:
        self.called = False
        self.records: List[ChunkGraphRecord] = []

    def upsert_chunk_graphs(self, records: List[ChunkGraphRecord]) -> None:
        self.called = True
        self.records.extend(records)

    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        return []


def test_ingest_service_writes_chunk_graph_records():
    vector_store = InMemoryVectorStore()
    graph_store = SpyGraphStore()
    embedder = FakeEmbedder()
    trace = FakeTrace()

    service = IngestService(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        trace=trace,
        chunk_size=10,
        chunk_overlap=0,
    )

    service.ingest(
        doc_id="doc_1",
        text="Graph retrieval with sqlite and fastapi.",
    )

    assert graph_store.called is True
    assert len(graph_store.records) > 0

    for i, record in enumerate(graph_store.records):
        assert record.chunk_id == f"doc_1#{i}"
        assert record.doc_id == "doc_1"
        assert record.text
        assert isinstance(record.terms, list)
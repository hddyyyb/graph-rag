from __future__ import annotations

from graph_rag.domain.models import RetrievedChunk
from graph_rag.infra.adapters import DefaultRetrievalPostProcessor




def test_sort():
    chunks = [RetrievedChunk(doc_id = 'doc_1', chunk_id = 'chunk_1', text = 'The first text', score = 0.55, source = "vector"),
            RetrievedChunk(doc_id = 'doc_2', chunk_id = 'chunk_2', text = 'The second text', score = 0.95, source = "vector"),
            RetrievedChunk(doc_id = 'doc_3', chunk_id = 'chunk_3', text = 'The third text', score = 0.75, source = "vector"),
            ]

    processor = DefaultRetrievalPostProcessor()
    result = processor.process(chunks, top_k=5)

    scores = [c.score for c in result.chunks]
    assert scores == [0.95, 0.75, 0.55]


def test_deduplication():
    chunks = [RetrievedChunk(doc_id = 'doc_1', chunk_id = 'chunk_1', text = 'The first text', score = 0.55, source = "vector"),
            RetrievedChunk(doc_id = 'doc_2', chunk_id = 'chunk_2', text = 'The second text', score = 0.95, source = "vector"),
            RetrievedChunk(doc_id = 'doc_1', chunk_id = 'chunk_1', text = 'The third text', score = 0.75, source = "vector"),
            ]
    processor = DefaultRetrievalPostProcessor()
    result = processor.process(chunks, top_k=5)
    assert len(result.chunks) == 2


def test_citations():
    chunks = [RetrievedChunk(doc_id = 'doc_1', chunk_id = 'chunk_1', text = 'The first text', score = 0.55, source = "vector"),
        RetrievedChunk(doc_id = 'doc_2', chunk_id = 'chunk_2', text = 'The second text', score = 0.95, source = "vector"),
        RetrievedChunk(doc_id = 'doc_3', chunk_id = 'chunk_3', text = 'The third text', score = 0.75, source = "vector"),
        ]
    processor = DefaultRetrievalPostProcessor()
    result = processor.process(chunks, top_k=5)
    assert len(result.citations) == 3
    assert result.citations[0]["score"] == 0.95
    assert result.citations[1]["score"] == 0.75
    assert result.citations[2]["score"] == 0.55
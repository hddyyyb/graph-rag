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


def test_process_keeps_highest_scored_chunk_when_duplicates_exist():

    duplicate_low = RetrievedChunk(doc_id = "doc_1", chunk_id = "chunk_1", source = "vector", score = 0.70, text = 'text 01')
    normal_chunk_1 = RetrievedChunk(doc_id = "doc_2", chunk_id = "chunk_2", source = "vector", score = 0.95, text = 'text 02')
    duplicate_high = RetrievedChunk(doc_id = "doc_1", chunk_id = "chunk_1", source = "vector", score = 0.92, text = 'text 03')
    normal_chunk_2 = RetrievedChunk(doc_id = "doc_3", chunk_id = "chunk_3", source = "vector", score = 0.85, text = 'text 04')
    
    processor = DefaultRetrievalPostProcessor()
    res = processor.process([duplicate_low, normal_chunk_1, duplicate_high, normal_chunk_2], 4)

    assert len(res.chunks) == 3
    target = [i for i in res.chunks if i.doc_id == "doc_1" and i.chunk_id =="chunk_1" and i.source == "vector" ]
    assert len(target) == 1
    assert target[0].score == 0.92
    scores = [c.score for c in res.chunks]
    assert scores == [0.95, 0.92, 0.85]

def test_process_applies_top_k_after_sort_and_dedup():
    duplicate_low = RetrievedChunk(doc_id = "doc_1", chunk_id = "chunk_1", source = "vector", score = 0.90, text = 'text 01')
    normal_chunk_1 = RetrievedChunk(doc_id = "doc_2", chunk_id = "chunk_2", source = "vector", score = 0.88, text = 'text 02')
    duplicate_high = RetrievedChunk(doc_id = "doc_1", chunk_id = "chunk_1", source = "vector", score = 0.92, text = 'text 03')
    normal_chunk_2 = RetrievedChunk(doc_id = "doc_3", chunk_id = "chunk_3", source = "vector", score = 0.85, text = 'text 04')
    
    processor = DefaultRetrievalPostProcessor()
    res = processor.process([duplicate_low, normal_chunk_1, duplicate_high, normal_chunk_2], 2)

    assert len(res.chunks) == 2
    score = [c.score for c in res.chunks]
    assert score == [0.92, 0.88]
    assert len(res.citations) == 2
    citation_keys = [(c["doc_id"], c["chunk_id"]) for c  in res.citations]
    assert citation_keys == [("doc_1", "chunk_1"), ("doc_2", "chunk_2")]                   



def test_min_score():
    duplicate_low = RetrievedChunk(doc_id = "doc_1", chunk_id = "chunk_1", source = "vector", score = 0.95, text = 'text 01')
    normal_chunk_1 = RetrievedChunk(doc_id = "doc_2", chunk_id = "chunk_1", source = "vector", score = 0.80, text = 'text 02')
    duplicate_high = RetrievedChunk(doc_id = "doc_3", chunk_id = "chunk_1", source = "vector", score = 0.60, text = 'text 03')
    normal_chunk_2 = RetrievedChunk(doc_id = "doc_4", chunk_id = "chunk_1", source = "vector", score = 0.40, text = 'text 04')
    
    processor = DefaultRetrievalPostProcessor()
    res = processor.process([duplicate_low, normal_chunk_1, duplicate_high, normal_chunk_2], 4, min_score=0.70)

    score = [c.score for c in res.chunks]
    assert len(score) == 2
    assert score[0] >= 0.70 and score[1] >= 0.70
    assert len(res.citations) == 2 


def test_min_score1():
    duplicate_low = RetrievedChunk(doc_id = "doc_1", chunk_id = "chunk_1", source = "vector", score = 0.95, text = 'text 01')
    normal_chunk_1 = RetrievedChunk(doc_id = "doc_2", chunk_id = "chunk_1", source = "vector", score = 0.80, text = 'text 02')
    duplicate_high = RetrievedChunk(doc_id = "doc_3", chunk_id = "chunk_1", source = "vector", score = 0.60, text = 'text 03')
    normal_chunk_2 = RetrievedChunk(doc_id = "doc_4", chunk_id = "chunk_1", source = "vector", score = 0.40, text = 'text 04')
    
    processor = DefaultRetrievalPostProcessor()
    res = processor.process([duplicate_low, normal_chunk_1, duplicate_high, normal_chunk_2], 4, min_score=None)

    score = [c.score for c in res.chunks]
    assert len(score) == 4
    assert len(res.citations) == 4


def test_min_score2():
    duplicate_low = RetrievedChunk(doc_id = "doc_1", chunk_id = "chunk_1", source = "vector", score = 0.90, text = 'text 01')
    normal_chunk_1 = RetrievedChunk(doc_id = "doc_2", chunk_id = "chunk_1", source = "vector", score = 0.70, text = 'text 02')
    duplicate_high = RetrievedChunk(doc_id = "doc_3", chunk_id = "chunk_1", source = "vector", score = 0.69, text = 'text 03')
    
    processor = DefaultRetrievalPostProcessor()
    res = processor.process([duplicate_low, normal_chunk_1, duplicate_high], 3, min_score=0.70)

    score = [c.score for c in res.chunks]
    assert len(score) == 2
    assert score[0] >= 0.70 and score[1] >= 0.70
    assert len(res.citations) == 2
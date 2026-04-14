from __future__ import annotations


from graph_rag.infra.adapters.fixed_length_chunker import FixedLengthChunker


def test_chunker_1_chunk() -> None:
    chunker = FixedLengthChunker(chunk_size=50, chunk_overlap=10)
    chunks = chunker.chunk("hello world", "doc1")
    
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "doc1#0"
    assert chunks[0].position == 0
    assert chunks[0].parent_id == "doc1"
    assert chunks[0].text == "hello world"

def test_chunker_long_text() -> None:
    text = "abcdefghij" * 100
    chunk_size = 100
    chunk_overlap = 20

    chunker = FixedLengthChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunker.chunk(text, "1")

    assert len(chunks) > 1
    assert chunks[0].chunk_id == "1#0"
    assert chunks[1].chunk_id == "1#1"
    assert all(chunk.parent_id == "1" for chunk in chunks)
    assert [chunk.position for chunk in chunks] == list(range(len(chunks)))

def test_chunker_overlap() -> None:
    text = "abcdefghijklmnopqrstuvwxyz"
    chunk_size = 10
    chunk_overlap = 2
    chunker = FixedLengthChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunker.chunk(text, "1")
    assert chunks[0].text == "abcdefghij"
    assert chunks[1].text == "ijklmnopqr"
    assert len(chunks) >= 2


def test_chunker_nullp() -> None:
    chunker = FixedLengthChunker(chunk_size=10, chunk_overlap=2)
    assert chunker.chunk("", "doc1") == []


from __future__ import annotations

from graph_rag.infra.adapters.recursive_chunker import RecursiveChunker


def test_recursive_chunker_paragraph_text() -> None:
    text = "A\n\nB\n\nC"
    chunker = RecursiveChunker(chunk_size=10, chunk_overlap=0)
    chunks = chunker.chunk(text, "doc1")

    assert len(chunks) == 1
    assert chunks[0].chunk_id == "doc1#0"
    assert chunks[0].position == 0
    assert chunks[0].parent_id == "doc1"
    assert chunks[0].text == "A\n\nB\n\nC"


def test_recursive_chunker_fallback_fixed_split() -> None:
    text = "abcdefghijklmno"
    chunker = RecursiveChunker(chunk_size=5, chunk_overlap=0)
    chunks = chunker.chunk(text, "doc1")

    assert len(chunks) == 3
    assert [c.text for c in chunks] == ["abcde", "fghij", "klmno"]
    assert [c.chunk_id for c in chunks] == ["doc1#0", "doc1#1", "doc1#2"]
    assert [c.position for c in chunks] == [0, 1, 2]
    assert all(c.parent_id == "doc1" for c in chunks)


def test_recursive_chunker_empty_text_returns_empty_list() -> None:
    chunker = RecursiveChunker(chunk_size=10, chunk_overlap=2)
    assert chunker.chunk("", "doc1") == []

def test_recursive_chunker_splits_long_paragraph_further() -> None:
    text = "This is a long sentence. This is another long sentence."
    chunker = RecursiveChunker(chunk_size=20, chunk_overlap=0)
    chunks = chunker.chunk(text, "doc1")

    assert len(chunks) > 1
    assert [c.position for c in chunks] == list(range(len(chunks)))
    assert all(len(c.text) <= 20 for c in chunks)
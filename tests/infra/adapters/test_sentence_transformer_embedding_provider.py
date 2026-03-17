from __future__ import annotations

from typing import List

from graph_rag.infra.adapters import SentenceTransformerEmbeddingProvider



def test_embed_query_returns_non_empty_vector():
    embedder = SentenceTransformerEmbeddingProvider()
    vec = embedder.embed_query('hello')
    assert isinstance(vec, list)
    assert len(vec) > 0
    assert isinstance(vec[0], float)


def test_embed_texts_returns_batch_vectors():
    embedder = SentenceTransformerEmbeddingProvider()
    vecs = embedder.embed_texts(["hello", "world"])
    assert isinstance(vecs, list)

    assert len(vecs) == 2
    assert isinstance(vecs[0], list)
    assert isinstance(vecs[1], list)
    assert len(vecs[0]) > 0
    assert len(vecs[0]) == len(vecs[1])


def test_embed_query_and_single_text_have_same_dimension():
    embedder = SentenceTransformerEmbeddingProvider()
    vecq = embedder.embed_query("hello")
    vect = embedder.embed_texts(["hello", "world"])[0]
    assert isinstance(vect, list)
    assert len(vecq) == len(vect)

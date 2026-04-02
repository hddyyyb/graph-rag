# `infra.adapters.milvus_store`

## Overview

This module currently provides `InMemoryVectorStore`, despite the filename suggesting a Milvus backend.

So at the moment, this file functions as an in-memory vector store adapter and not as a real Milvus integration.

## Top-Level Helper

## `_cosine(a: List[float], b: List[float]) -> float`

Computes cosine similarity between two vectors.

### Inputs
- `a`: first vector
- `b`: second vector

### Output
- cosine similarity score as `float`

### Behavior
- returns `0.0` when one of the norms is zero

## Class

## `InMemoryVectorStore`

### Purpose

This adapter is a memory-based implementation of `VectorStorePort`.

It is used to:
- validate vector retrieval flow
- support early development
- avoid external vector database dependencies

## Internal Storage

```python
self._data: Dict[Tuple[str, str], Tuple[str, List[float]]]
```

Meaning:

- key: `(doc_id, chunk_id)`
- value: `(text, embedding)`

## Public Methods

### `upsert(doc_id: str, chunks: List[str], embeddings: List[List[float]]) -> None`

Stores chunks and embeddings in memory.

### Behavior
For each `(text, embedding)` pair:
- assigns a chunk id like `c0`, `c1`, `c2`, ...
- stores the tuple under `(doc_id, chunk_id)`

### Inputs
- `doc_id`: document identifier
- `chunks`: chunk text list
- `embeddings`: aligned embedding list

### Notes
- assumes `chunks` and `embeddings` are aligned by position
- current implementation does not explicitly validate mismatched lengths

---

### `search(...) -> List[RetrievedChunk]`

Signature:

```python
search(
    query_embedding: List[float],
    top_k: int,
    options: Optional[SearchOptions] = None,
    filter_doc_id: Optional[str] = None,
    min_score: Optional[float] = None,
) -> List[RetrievedChunk]
```

### Behavior
1. normalizes search options
2. iterates over all stored chunks
3. optionally filters by `doc_id`
4. computes cosine similarity
5. optionally filters by `min_score`
6. sorts results descending by score
7. returns top `k` as `RetrievedChunk`

### Output Source Tag
Returned chunks use:

```python
source="memory"
```

## Example

```python
store = InMemoryVectorStore()

store.upsert(
    doc_id="doc1",
    chunks=["hello world", "graph rag"],
    embeddings=[[1.0, 0.0], [0.0, 1.0]],
)

results = store.search(
    query_embedding=[1.0, 0.0],
    top_k=2,
)
```

## Strengths

- zero external dependency
- easy to understand
- good for tests and demos

## Limitations

- no persistence
- no ANN index
- brute-force full scan
- filename and implementation are currently inconsistent

## Suggested Future Direction

If this file is later upgraded into a real Milvus adapter, it should preserve the same `VectorStorePort` contract while replacing internal storage and similarity search with Milvus operations.
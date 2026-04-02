# `infra.adapters.sqlite_vector_store`

## Overview

This module provides `SQLiteVectorStore`, a SQLite-backed vector store adapter.

It stores chunk embeddings in a local SQLite database and performs retrieval using pure Python cosine similarity.

This is a lightweight persistent vector backend for local development and integration testing.

## Class

## `SQLiteVectorStore`

### Purpose

This adapter persists chunk embeddings in a file-based database while preserving a simple `upsert/search` interface.

It is useful for:
- local persistence
- integration testing
- verifying real retrieval paths without introducing a full vector database

## Constructor

### `__init__(db_path: str)`

**Parameters**
- `db_path`: SQLite database file path

### Behavior
- opens a SQLite connection with `check_same_thread=False`
- creates a `chunks` table if it does not already exist

### Table Schema

```sql
CREATE TABLE IF NOT EXISTS chunks (
    doc_id TEXT,
    chunk_id TEXT,
    text TEXT,
    embedding TEXT,
    PRIMARY KEY (doc_id, chunk_id)
)
```

## Public Methods

### `upsert(doc_id: str, chunks: List[str], embeddings: List[List[float]]) -> None`

Writes chunk text and embeddings for one document.

### Behavior
1. validates that `chunks` and `embeddings` have the same length
2. deletes old rows for the target `doc_id`
3. inserts fresh rows using `executemany`
4. commits the transaction

### Chunk ID Format

Each chunk id is generated as:

```python
f"{doc_id}#{i}"
```

### Storage Format

Embeddings are serialized with `json.dumps(...)` before being written to SQLite.

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
2. returns `[]` if `top_k <= 0`
3. fetches rows from SQLite
4. optionally filters by `doc_id`
5. deserializes embedding JSON
6. computes cosine similarity
7. applies optional `min_score`
8. sorts descending by score
9. returns top `k`

### Output Source Tag

Returned chunks use:

```python
source="sqlite"
```

## Internal Method

### `_cosine(a: List[float], b: List[float]) -> float`

Computes cosine similarity in pure Python.

Returns `0.0` if either vector norm is zero.

## Example

```python
store = SQLiteVectorStore("graph_rag.db")

store.upsert(
    doc_id="doc1",
    chunks=["hello", "world"],
    embeddings=[[1.0, 0.0], [0.0, 1.0]],
)

results = store.search(
    query_embedding=[1.0, 0.0],
    top_k=2,
)
```

## Strengths

- persistent local storage
- easy to inspect
- no external vector service required
- suitable for integration tests

## Limitations

- brute-force retrieval
- embeddings stored as JSON text
- no ANN indexing
- not intended for large-scale production workloads
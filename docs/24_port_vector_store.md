# Vector Store Port

## Overview

This file defines the abstraction for vector storage and vector retrieval in the GraphRAG system.

It contains:

- the `SearchOptions` model
- the `normalize_search_options()` helper
- the `VectorStorePort` interface

Together, these define the contract for vector-based retrieval backends.

---

## SearchOptions

### Purpose

`SearchOptions` is an immutable configuration object for vector search behavior.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SearchOptions:
    filter_doc_id: Optional[str] = None
    min_score: Optional[float] = None
```

---

## Fields

### `filter_doc_id`

Optional document ID filter.

Type:

```python
Optional[str]
```

If provided, search results should be restricted to a specific document.

### `min_score`

Optional minimum score threshold.

Type:

```python
Optional[float]
```

If provided, results below this score can be filtered out.

---

## normalize_search_options

### Purpose

This helper merges explicit function arguments with an optional `SearchOptions` object into one normalized result.

```python
def normalize_search_options(
    options: Optional[SearchOptions] = None,
    filter_doc_id: Optional[str] = None,
    min_score: Optional[float] = None,
) -> SearchOptions:
    base = options or SearchOptions()
    return SearchOptions(
        filter_doc_id=filter_doc_id if filter_doc_id is not None else base.filter_doc_id,
        min_score=min_score if min_score is not None else base.min_score,
    )
```

### Behavior

It applies the following rule:

- if an explicit argument is provided, it overrides `options`
- otherwise, it falls back to values from `options`
- if neither is provided, defaults are used

### Why It Matters

This makes search configuration easier to reason about while still supporting explicit override behavior.

---

## VectorStorePort

### Interface

```python
class VectorStorePort(Protocol):
    def upsert(
        self,
        doc_id: str,
        chunks: List[str],
        embeddings: List[List[float]]
    ) -> None:
        ...

    def search(
        self,
        query_embedding: List[float],
        top_k: int,
        options: Optional[SearchOptions] = None,
        filter_doc_id: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        ...
```

---

## Methods

### `upsert(doc_id, chunks, embeddings)`

Writes document chunks and embeddings into the vector store.

```python
def upsert(
    self,
    doc_id: str,
    chunks: List[str],
    embeddings: List[List[float]]
) -> None:
    ...
```

#### Parameters

- `doc_id`: Document identifier
- `chunks`: Chunk text list
- `embeddings`: Embedding vectors corresponding to the chunks

#### Responsibility

A concrete implementation should store chunk text and embeddings in a way that supports later similarity search.

---

### `search(query_embedding, top_k, options=None, filter_doc_id=None, min_score=None)`

Performs vector similarity retrieval.

```python
def search(
    self,
    query_embedding: List[float],
    top_k: int,
    options: Optional[SearchOptions] = None,
    filter_doc_id: Optional[str] = None,
    min_score: Optional[float] = None,
) -> List[RetrievedChunk]:
    ...
```

#### Parameters

- `query_embedding`: Query vector
- `top_k`: Maximum number of retrieval results
- `options`: Optional `SearchOptions` object
- `filter_doc_id`: Optional explicit document filter
- `min_score`: Optional explicit score threshold

#### Returns

- `List[RetrievedChunk]`: Retrieved chunk list

---

## Design Notes

This interface is designed to support multiple backends such as:

- in-memory vector store
- SQLite-based vector store
- production-grade vector database

The application layer does not need to know which backend is used.

---

## Typical Flow

```text
Query
  -> EmbeddingProviderPort.embed_query()
  -> VectorStorePort.search()
  -> List[RetrievedChunk]
```

---

## Example Usage

```python
results = vector_store.search(
    query_embedding=[0.1, 0.2, 0.3],
    top_k=5,
    min_score=0.25,
)
```

Or with options:

```python
options = SearchOptions(filter_doc_id="doc1", min_score=0.3)

results = vector_store.search(
    query_embedding=[0.1, 0.2, 0.3],
    top_k=5,
    options=options,
)
```

---

## Why This Design Works Well

### 1. Flexible configuration

Supports both object-style options and direct keyword overrides.

### 2. Backend independence

The application layer stays decoupled from concrete vector databases.

### 3. Clean retrieval contract

Input and output are explicit and easy to test.

---

## Summary

This file defines the vector retrieval contract of the system.

It includes:

- `SearchOptions`: immutable search configuration
- `normalize_search_options()`: option normalization helper
- `VectorStorePort`: vector storage and search interface

Together, they form the core abstraction for vector-based retrieval in GraphRAG.
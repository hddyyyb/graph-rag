# Embedding Provider Port

## Overview

This file defines the `EmbeddingProviderPort`, which is the abstraction for embedding generation in the GraphRAG system.

It provides two main capabilities:

- embedding multiple texts
- embedding a single query

This port isolates the application layer from the concrete embedding backend.

---

## Interface

```python
from __future__ import annotations

from typing import List, Protocol


class EmbeddingProviderPort(Protocol):
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        ...

    def embed_query(self, query: str) -> List[float]:
        ...
```

---

## Methods

### `embed_texts(texts)`

Embeds multiple texts into vector representations.

```python
def embed_texts(self, texts: List[str]) -> List[List[float]]:
    ...
```

#### Parameters

- `texts`: List of input text strings

#### Returns

- `List[List[float]]`: List of embedding vectors

Each output vector corresponds to one input text.

---

### `embed_query(query)`

Embeds a single user query into a vector representation.

```python
def embed_query(self, query: str) -> List[float]:
    ...
```

#### Parameters

- `query`: Query string

#### Returns

- `List[float]`: Query embedding vector

---

## Why Two Methods Exist

Although both texts and queries are embedded, separating the interface into two methods has practical value.

### `embed_texts`

Used for ingest-time chunk embedding.

### `embed_query`

Used for query-time retrieval embedding.

This separation makes the application code clearer and leaves room for future implementation differences.

For example, some systems may want:

- different preprocessing for documents and queries
- different models or prompt prefixes
- different batching strategies

---

## Typical Flow

### Ingest flow

```text
Document
  -> chunking
  -> EmbeddingProviderPort.embed_texts(chunks)
  -> VectorStorePort.upsert(...)
```

### Query flow

```text
Query
  -> EmbeddingProviderPort.embed_query(query)
  -> VectorStorePort.search(...)
```

---

## Example Usage

```python
chunk_embeddings = embedding_provider.embed_texts([
    "GraphRAG combines vector retrieval and graph retrieval.",
    "Neo4j can be used as a graph backend.",
])

query_embedding = embedding_provider.embed_query("What is GraphRAG?")
```

---

## Backend Independence

Concrete implementations may include:

- fake embedding provider for tests
- local sentence-transformers model
- cloud embedding API
- other embedding backends

The application layer does not need to change when switching among them.

---

## Engineering Benefits

### 1. Decoupling

Embedding logic stays outside the application layer.

### 2. Testability

Fake embedding providers can be injected in tests.

### 3. Flexibility

Different embedding backends can be swapped without changing orchestration code.

---

## Summary

`EmbeddingProviderPort` defines the embedding-generation boundary of the GraphRAG system.

It supports both ingest-time and query-time embedding while keeping the application layer clean and backend-independent.
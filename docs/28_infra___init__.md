# `infra.adapters.__init__`

## Overview

This module is the package export surface for the `graph_rag.infra.adapters` package.

It re-exports the concrete infrastructure implementations used by the composition root, tests, and API layer so callers can import adapters from a single location instead of importing each file individually.

## Purpose

The file improves package ergonomics and keeps the infrastructure layer easy to wire.

Typical usage:

```python
from graph_rag.infra.adapters import (
    InMemoryVectorStore,
    InMemoryGraphStore,
    SQLiteVectorStore,
    Neo4jGraphStore,
    FakeLLM,
)
```

## Exported Adapters

### Embedding providers
- `HashEmbeddingProvider`
- `SentenceTransformerEmbeddingProvider`
- `FakeEmbeddingV2`

### Vector stores
- `InMemoryVectorStore`
- `SQLiteVectorStore`

### Graph stores
- `InMemoryGraphStore`
- `Neo4jGraphStore`

### Time providers
- `SystemClock`
- `FixedClock`

### Kernel / answer generation
- `SimpleKernel`
- `SimpleRAGKernel`
- `FakeKernel`

### LLM adapters
- `FakeLLM`
- `LocalLLM`
- `OpenAILLM`

### Retrieval post-processing
- `DefaultRetrievalPostProcessor`

## Design Notes

- This module contains no business logic.
- It acts as a package-level import aggregator.
- It is especially useful for dependency injection and container wiring.

## `__all__`

The module explicitly defines `__all__`, which means only the intended public adapter symbols are exported when using wildcard imports.

## When to Modify This File

Update this file when:
- a new adapter is added to `infra/adapters`
- an old adapter is removed
- you want a concrete adapter to be publicly importable from the package root

## Example

```python
from graph_rag.infra.adapters import SQLiteVectorStore, OpenAILLM

store = SQLiteVectorStore(db_path="data/graph_rag.db")
llm = OpenAILLM(api_key="your-api-key")
```
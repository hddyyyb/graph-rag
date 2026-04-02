# Graph Store Port

## Overview

This file defines the `GraphStorePort`, which is the abstraction for graph-based storage and graph retrieval in the GraphRAG system.

It specifies the capabilities required for graph retrieval support:

- writing chunk-based graph records
- retrieving chunks using query-driven graph logic
- exposing the latest graph debug information

This port allows the application layer to use graph retrieval without depending on a specific graph backend.

---

## Interface

```python
from __future__ import annotations

from typing import Dict, List, Optional, Protocol, Any

from graph_rag.domain.models import RetrievedChunk
from graph_rag.domain.graph_models import ChunkGraphRecord
from graph_rag.domain.graph_debug_models import GraphSearchResult


class GraphStorePort(Protocol):
    def upsert_chunk_graphs(self, records: List[ChunkGraphRecord]) -> None:
        ...

    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        ...

    def get_last_debug(self) -> Optional[Dict[str, Any]]:
        ...
```

---

## Methods

### `upsert_chunk_graphs(records)`

Writes graph-ready chunk records into the graph store.

```python
def upsert_chunk_graphs(self, records: List[ChunkGraphRecord]) -> None:
    ...
```

#### Parameters

- `records`: List of `ChunkGraphRecord` objects

#### Responsibility

A concrete implementation should use these records to build or update graph structure.

This may include:

- chunk nodes
- term nodes
- chunk-term links
- term-term co-occurrence edges

---

### `search(query, top_k)`

Performs graph retrieval using the input query.

```python
def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
    ...
```

#### Parameters

- `query`: Input query text
- `top_k`: Maximum number of results to return

#### Returns

- `List[RetrievedChunk]`: Retrieved chunk list

#### Responsibility

The graph store implementation is responsible for using graph structure to retrieve relevant chunks.

Depending on the backend and algorithm, this may involve:

- direct term matching
- graph expansion
- weighted graph scoring
- structural retrieval logic

---

### `get_last_debug()`

Returns the most recent graph retrieval debug payload.

```python
def get_last_debug(self) -> Optional[Dict[str, Any]]:
    ...
```

#### Returns

- `Optional[Dict[str, Any]]`: Latest graph debug information, if available

#### Responsibility

This method allows the application layer to fetch structured debug information from the most recent graph search.

It is useful for:

- observability
- testing
- backend consistency checking
- query debug output

---

## Required Capabilities

If the application layer wants to support graph retrieval, the graph system must support at least two core operations:

### 1. Graph writing

Documents must be written into graph-ready structure.

### 2. Graph search

Queries must be able to retrieve chunks through graph logic.

---

## Comparison with VectorStorePort

The file itself highlights the conceptual difference:

```text
VectorStore           GraphStore
Input   embedding vectors     query text
Logic   similarity retrieval  structural relationship retrieval
Output  RetrievedChunk        RetrievedChunk
```

### Vector retrieval

- input: query embedding
- logic: similarity search
- output: retrieved chunks

### Graph retrieval

- input: query text
- logic: structural or relationship-based retrieval
- output: retrieved chunks

This makes both stores complementary retrieval signals in GraphRAG.

---

## Note on GraphSearchResult Import

The file imports `GraphSearchResult`, but the current interface returns:

- `List[RetrievedChunk]` from `search()`
- optional raw debug dictionary from `get_last_debug()`

So the design currently exposes graph debug and hits through separate methods instead of returning a single bundled result directly.

This is a practical interface choice, although a future refactor could also choose to return a structured `GraphSearchResult`.

---

## Example Usage

```python
graph_store.upsert_chunk_graphs([
    ChunkGraphRecord(
        chunk_id="c1",
        doc_id="doc1",
        text="GraphRAG combines graph retrieval and vector retrieval.",
        terms=["graphrag", "graph", "vector", "retrieval"],
    )
])

hits = graph_store.search("graph retrieval", top_k=5)
debug = graph_store.get_last_debug()
```

---

## Typical Flow

### Ingest flow

```text
Chunk text
  -> term extraction
  -> ChunkGraphRecord
  -> GraphStorePort.upsert_chunk_graphs(...)
```

### Query flow

```text
Query
  -> GraphStorePort.search(...)
  -> RetrievedChunk list
  -> GraphStorePort.get_last_debug()
```

---

## Engineering Benefits

### 1. Backend independence

The application layer can work with:

- in-memory graph store
- Neo4j graph store
- future graph backends

without changing business logic.

### 2. Explainability support

The explicit debug interface makes graph retrieval more observable.

### 3. Clear retrieval role

The graph store is responsible for structural retrieval rather than vector similarity.

---

## Summary

`GraphStorePort` defines the graph retrieval boundary of the GraphRAG system.

It standardizes three essential graph capabilities:

- graph ingestion via `upsert_chunk_graphs`
- graph retrieval via `search`
- debug exposure via `get_last_debug`

This makes graph retrieval modular, explainable, and easy to evolve.
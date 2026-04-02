# Graph Domain Models

## Overview

This file defines the core graph-related domain objects used by the graph retrieval subsystem.

These models describe:

- graph nodes
- graph edges
- chunk-level graph records
- graph retrieval debug/result containers

They are designed to support graph construction and graph-based retrieval in a backend-independent way.

---

## Design Goals

The models in this file aim to:

- keep graph concepts explicit
- make graph ingestion contracts stable
- separate graph modeling from backend implementation details
- support both in-memory and database-backed graph stores
- provide structured outputs for graph retrieval

---

## Classes

### GraphNode

Represents a node in the graph.

```python
@dataclass(frozen=True)
class GraphNode:
    node_id: str
    name: str
    node_type: str = "keyword"
```

#### Fields

- `node_id`: Unique node identifier
- `name`: Human-readable node name
- `node_type`: Node category, default is `"keyword"`

#### Notes

In the current system, nodes are primarily keyword-like terms extracted from chunks.

---

### GraphEdge

Represents an edge between two graph nodes.

```python
@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str = "co_occurrence"
    weight: float = 1.0
```

#### Fields

- `edge_id`: Unique edge identifier
- `source_node_id`: Source node ID
- `target_node_id`: Target node ID
- `edge_type`: Relationship type, default is `"co_occurrence"`
- `weight`: Edge strength, default is `1.0`

#### Notes

The current design mainly uses co-occurrence relationships between terms.

The `weight` field allows the system to represent stronger or weaker semantic association signals.

---

### ChunkGraphRecord

Represents the graph-ready data extracted from a chunk.

```python
@dataclass(frozen=True)
class ChunkGraphRecord:
    chunk_id: str
    doc_id: str
    text: str
    terms: List[str] = None
```

#### Fields

- `chunk_id`: Chunk identifier
- `doc_id`: Parent document identifier
- `text`: Original chunk text
- `terms`: Extracted terms associated with the chunk

#### Important Design Detail

The `terms` field indicates that **term extraction is already completed outside the GraphStore**.

This means the graph store is not responsible for NLP extraction itself. Instead, it receives already prepared chunk-term data.

That design has several advantages:

- separates extraction from storage
- keeps graph backend simpler
- makes testing easier
- avoids coupling graph storage to a specific term extraction strategy

---

### GraphSearchDebug

Represents debug information for graph retrieval.

```python
@dataclass(frozen=True)
class GraphSearchDebug:
    query: str
    matched_terms: List[str]
    candidate_chunk_ids: List[str]
```

#### Fields

- `query`: Original input query
- `matched_terms`: Terms from the query that matched the graph
- `candidate_chunk_ids`: Candidate chunk IDs identified through graph retrieval

#### Usage

This model is useful for observability and debugging of graph retrieval behavior.

---

### GraphSearchResult

Represents the output of a graph retrieval call.

```python
@dataclass(frozen=True)
class GraphSearchResult:
    hits: List[RetrievedChunk]
    debug: Optional[GraphSearchDebug] = None
```

#### Fields

- `hits`: Retrieved chunk list
- `debug`: Optional debug information for graph retrieval

#### Usage

This is the structured return type for graph retrieval backends.

It keeps retrieval results and debug information bundled together.

---

## Data Flow Role

These models usually appear in the following flow:

### Ingest flow

```text
Document
  -> Chunk
  -> Term Extraction
  -> ChunkGraphRecord
  -> GraphStore
```

### Query flow

```text
Query
  -> Query Terms
  -> Graph Search
  -> GraphSearchResult
  -> RetrievedChunk list
```

---

## Example

```python
record = ChunkGraphRecord(
    chunk_id="chunk_01",
    doc_id="doc_001",
    text="FastAPI integrates well with GraphRAG services.",
    terms=["fastapi", "graphrag", "services"],
)

node = GraphNode(
    node_id="term_fastapi",
    name="fastapi",
)

edge = GraphEdge(
    edge_id="edge_001",
    source_node_id="term_fastapi",
    target_node_id="term_graphrag",
    weight=2.0,
)
```

---

## Engineering Significance

This file is important because it defines the **graph-side internal contract** of the system.

Without these models, graph retrieval logic would become tightly coupled to backend-specific representations such as:

- Python dictionaries
- Neo4j records
- ad hoc query outputs

By introducing stable domain models, the system stays cleaner and easier to evolve.

---

## Current Scope

The current graph modeling is intentionally minimal:

- node type is term/keyword oriented
- edge type is mainly co-occurrence
- chunk records are the central ingest unit
- retrieval results are chunk-based

This is enough to support the current GraphRAG graph retrieval stage while leaving room for future upgrades such as:

- entity-level modeling
- richer relation types
- multi-hop reasoning
- path-aware ranking

---

## Summary

This file defines the main graph-side business objects:

- `GraphNode`: graph node
- `GraphEdge`: graph edge
- `ChunkGraphRecord`: chunk + extracted terms for graph ingestion
- `GraphSearchDebug`: graph retrieval debug info
- `GraphSearchResult`: graph retrieval output

Together, they provide a clean and extensible graph modeling foundation for the GraphRAG system.
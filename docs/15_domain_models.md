# Domain Models

## Overview

This file defines the core business objects used inside the GraphRAG system.

These models are **internal domain/application objects**, which means they are used for communication between layers inside the system rather than for direct HTTP request/response handling.

The main goals of these models are:

- provide stable internal data contracts
- make service input/output explicit
- keep business data structures lightweight and immutable
- separate internal models from external API schemas

---

## Design Notes

All objects in this file are implemented with Python `dataclass` and `frozen=True`.

This means:

- instances are easy to construct
- fields are explicit
- objects are immutable after creation
- the models are suitable for predictable engineering workflows

Example:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class IngestResult:
    doc_id: str
    chunks: int
```

This is roughly equivalent to a manually written class, but much cleaner.

---

## Classes

### Document

Represents a raw input document before chunking or retrieval.

```python
@dataclass(frozen=True)
class Document:
    doc_id: str
    text: str
    metadata: Dict[str, Any]
```

#### Fields

- `doc_id`: Unique document identifier
- `text`: Full raw document text
- `metadata`: Arbitrary document metadata, such as title, source, author, or tags

#### Usage

This model is typically used as the input unit for the ingest pipeline.

---

### IngestResult

Represents the result returned by the ingest service.

```python
@dataclass(frozen=True)
class IngestResult:
    doc_id: str
    chunks: int
```

#### Fields

- `doc_id`: Identifier of the ingested document
- `chunks`: Number of chunks generated from the document

#### Usage

This model is used to summarize ingest success in a lightweight way.

---

### RetrievedChunk

Represents a retrieved chunk candidate produced by retrieval backends.

```python
@dataclass(frozen=True)
class RetrievedChunk:
    doc_id: str
    chunk_id: str
    text: str
    score: float
    source: str
```

#### Fields

- `doc_id`: Source document ID
- `chunk_id`: Unique chunk ID within the document
- `text`: Chunk text content
- `score`: Retrieval score assigned by the backend or fusion stage
- `source`: Retrieval source, typically `"vector"` or `"graph"`

#### Usage

This is one of the most important internal models in the system.

It is used for:

- vector retrieval results
- graph retrieval results
- merged/fused retrieval candidates
- post-processing and ranking

---

### Answer

Represents the final response returned by the query pipeline.

```python
@dataclass(frozen=True)
class Answer:
    answer: str
    trace_id: str
    retrieval_debug: Dict[str, Any]
    citations: Optional[List[Dict[str, Any]]] = None
```

#### Fields

- `answer`: Final generated answer text
- `trace_id`: Trace identifier used for observability and debugging
- `retrieval_debug`: Structured debug information about retrieval execution
- `citations`: Optional citation list attached to the answer

#### Usage

This model is typically returned by `QueryService`.

It combines:

- final LLM output
- request-level trace information
- retrieval observability data
- optional citation metadata

---

## Layer Responsibility

These models belong to the **domain/application internal contract layer**.

They are different from API schemas:

- `api/schemas`: external HTTP request/response models
- `domain/models`: internal business objects

This separation helps keep the system clean and maintainable.

---

## Example

```python
document = Document(
    doc_id="doc_001",
    text="GraphRAG combines vector retrieval and graph retrieval.",
    metadata={"source": "demo", "lang": "en"},
)

retrieved = RetrievedChunk(
    doc_id="doc_001",
    chunk_id="chunk_01",
    text="GraphRAG combines vector retrieval and graph retrieval.",
    score=0.92,
    source="vector",
)

answer = Answer(
    answer="GraphRAG combines vector and graph-based retrieval signals.",
    trace_id="trace-123",
    retrieval_debug={"vector_count": 1, "graph_count": 0},
    citations=[{"doc_id": "doc_001", "chunk_id": "chunk_01"}],
)
```

---

## Summary

This file defines the foundational internal data models of the system:

- `Document`: raw input document
- `IngestResult`: ingest output summary
- `RetrievedChunk`: retrieval candidate
- `Answer`: final query output

Together, they provide a clear and stable data contract across the GraphRAG pipeline.
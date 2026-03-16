
# Interfaces

This document defines the core service interfaces of the GraphRAG system.  
The goal is to ensure **clear abstraction boundaries**, **replaceable infrastructure components**, and **consistent observability and error handling** across the system.

---

# 0. Design Principles

The interface layer follows several architectural principles:

- **Business layers depend only on abstractions** (Protocol / ABC) and must not depend directly on specific implementations such as Neo4j, Milvus, or LlamaIndex.
- **Interfaces are named using business actions**, such as `ingest`, `query`, `update`, and `delete`.
- **All methods must include `trace_id`** as a parameter (or receive it through context injection) to support observability and tracing.
- **Errors must be categorized** to enable reliable error handling and retries:

| Error Type | Description |
|------------|-------------|
| InvalidArgument | Request parameters are invalid |
| Transient | Temporary error that may succeed on retry |
| Unavailable | External dependency unavailable |
| Conflict | Idempotency or concurrency conflict |
| Internal | Unexpected internal system error |

---

# 1. Core Domain Data Structures

Suggested core domain models used across interfaces:

### Document

```text
Document {
  doc_id
  content
  metadata
  content_hash
}

### Chunk

```text
Chunk {
  chunk_id
  doc_id
  text
  index
  metadata
}
```

### RetrievalResult

```text
RetrievalResult {
  chunks
  debug
}
```

### Answer

```text
Answer {
  answer
  citations
  trace_id
  timings
}
```

---

# 2. Interface List (≤ 8)

The following interfaces define the core extension points of the system.

---

## 2.1 ConfigProvider

Provides application configuration.

```
get() -> AppConfig
```

---

## 2.2 EmbeddingProvider

Responsible for generating vector embeddings from text.

```
embed_texts(texts: list[str], trace_id: str) -> list[list[float]]
```

---

## 2.3 VectorStore

Responsible for vector storage and semantic search.

```
upsert(chunks: list[Chunk], vectors: list[list[float]], trace_id: str) -> None
delete_by_doc(doc_id: str, trace_id: str) -> None
search(query: str, top_k: int, filters: dict, trace_id: str) -> RetrievalResult
```

---

## 2.4 GraphStore

Responsible for graph-based storage and retrieval.

```
upsert_document(doc: Document, trace_id: str) -> None
upsert_chunks(chunks: list[Chunk], trace_id: str) -> None
link_doc_chunks(doc_id: str, chunk_ids: list[str], trace_id: str) -> None
delete_by_doc(doc_id: str, trace_id: str) -> None
search(query: str, top_k: int, filters: dict, trace_id: str) -> RetrievalResult
```

---

## 2.5 Kernel

Core reasoning kernel that encapsulates the LlamaIndex interaction layer.

This interface hides the underlying LLM orchestration framework.

```
answer(query: str, chunks: list[Chunk], trace_id: str) -> Answer
```

---

## 2.6 IngestService (Use Case)

Business use case responsible for document ingestion.

```
ingest(doc: Document, trace_id: str) -> {
    ingest_id,
    chunk_count,
    timings
}
```

---

## 2.7 QueryService (Use Case)

Business use case responsible for query execution.

```
query(query: str, mode: str, top_k: int, filters: dict, trace_id: str) -> Answer
```

---

## 2.8 Observability

Provides tracing, logging, and timing capabilities for system observability.

```
new_trace_id() -> str
log(event: dict) -> None
timer(name: str) -> context_manager
```


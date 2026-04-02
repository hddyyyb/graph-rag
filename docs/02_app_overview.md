# Application Layer Overview

## 1. Layer Responsibility

`src/graph_rag/application` is responsible for **business orchestration**.

This layer does not implement infrastructure details directly.  
Instead, it coordinates the full workflow through abstract Ports.

Main responsibilities:

- organize ingest flow
- organize query flow
- normalize request options
- coordinate retrieval / fusion / postprocess / generation
- expose system-level behavior in a structured way

---

## 2. Main Files

### `ingest_service.py`
Responsible for the end-to-end ingest workflow:

- validate input
- chunk text
- generate embeddings
- write vector store
- build chunk-level graph records
- write graph store

---

### `query_option.py`
Defines query-time configuration:

- top_k
- min_score
- enable_vector
- enable_graph

Also provides normalization logic so callers can combine:

- a full `QueryOptions` object
- or per-call override parameters

---

### `query_service.py`
Responsible for the end-to-end query workflow:

- validate query
- normalize options
- generate query embedding
- retrieve vector candidates
- retrieve graph candidates
- fuse retrieval results
- post-process candidates
- call kernel to generate final answer
- build structured retrieval debug payload

---

## 3. Dependency Direction

Application depends on:

- Domain models
- Domain errors
- Ports

Application does NOT depend on:

- concrete SQLite implementation
- concrete Neo4j implementation
- concrete sentence-transformers implementation
- concrete OpenAI / local LLM implementation

This keeps orchestration stable while allowing backend swapping.

---

## 4. Ports Used by Application Layer

Core Ports used in this layer include:

- `EmbeddingProviderPort`
- `VectorStorePort`
- `GraphStorePort`
- `RAGKernelPort`
- `RetrievalPostProcessorPort`
- `TracePort`

These Ports allow the application layer to stay decoupled from infrastructure.

---

## 5. Key Design Style

The application layer follows an orchestration-first design:

- each service focuses on workflow composition
- validation happens early
- failures are mapped into structured business errors
- timings / stats / trace signals are captured during execution
- retrieval behavior is made observable via `retrieval_debug`

---

## 6. Why This Layer Matters

This layer is the core of the system’s engineering value.

It shows how to build a GraphRAG system that is:

- modular
- testable
- explainable
- backend-agnostic
- observable

In other words, this layer is what turns the project from “a set of components” into “a working system”.
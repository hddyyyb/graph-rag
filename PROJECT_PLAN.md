# 🚀 PROJECT_PLAN.md

## 0. Project Positioning

This project is an industrial-grade GraphRAG system prototype built with Clean Architecture.

It includes:
- API Layer (FastAPI)
- Application Layer (QueryService / IngestService)
- Domain Models
- Ports (interfaces)
- Infra (Embedding / Vector / Graph / LLM)

⚠️ Current status:
This is no longer just an architecture skeleton.
It is now a partially functional GraphRAG system with real ingest/query pipelines and partially real infra.

---

## 1. Current System Snapshot

### 1.1 API Layer (COMPLETED)

- FastAPI application ready
- Endpoints:
  - POST /ingest
  - POST /query
  - GET /health
- Swagger UI available
- Middleware:
  - trace_id
  - logging
  - error mapping

---

### 1.2 Application Layer (COMPLETED)

#### QueryService
- normalize query
- validate input
- embedding
- hybrid retrieval (vector + graph)
- post-processing:
  - ranking
  - min_score filtering
  - deduplication
  - top_k
- LLM answer generation
- debug info:
  - timings
  - retrieval stats
  - citations

#### IngestService
- validate document
- chunk text
- embedding
- write vector store
- write graph store

---

### 1.3 Observability (COMPLETED)

- embedding_time
- vector_retrieval_time
- graph_retrieval_time
- postprocess_time
- llm_generation_time
- trace_id tracking
- retrieval debug structure available in query response

---

### 1.4 Infra Layer (PARTIALLY REAL)

#### Embedding
- SentenceTransformerEmbeddingProvider implemented
- system already supports real embedding generation
- fake embedding still exists only as an alternative backend for tests / lightweight runs

#### Vector Store
- SQLiteVectorStore implemented
- supports persistent upsert
- supports cosine similarity search
- supports filter_doc_id / min_score / top_k
- already wired into container as a selectable runtime backend
- real vector retrieval path is available

#### Graph Store
- currently InMemoryGraphStore
- NOT real Neo4j yet
- graph ingestion and retrieval are still at placeholder stage

#### LLM
- fake / local / OpenAI backends can be switched in container
- runtime backend selection pattern is already established
---

### 1.5 Runtime Wiring (PARTIAL BUT WORKING)

- container / composition root implemented
- backend switching already supported for:
  - llm backend
  - vector store backend
- ingest and query services receive dependencies through the same container
- when vector_store_backend="sqlite", ingest and query already share the same real SQLiteVectorStore instance

---

### 1.6 Testing

- unit tests available
- service-level tests available
- API smoke tests available
- unit tests available
- service-level tests available
- API smoke tests available

- real SQLite vector retrieval integration tests implemented:
  - vector-only closed-loop verification
  - top_k behavior verification
  - min_score filtering verification

- test system now covers:
  - service orchestration (fake-based)
  - vector store correctness (SQLite)
  - real integration behavior (embedding + SQLite)


---

## 2. Reality Check

This system is:

✅ API-ready  
✅ Pipeline-complete  
✅ Real embedding available  
✅ Real vector store available  
⚠️ Graph still fake/in-memory  
✅ Real vector retrieval closed loop validated with dedicated integration tests
❌ Not fully production-ready

---

## 3. Core Gaps

### 3.1 Graph Backend Missing
- no Neo4jGraphStore yet
- no graph schema yet
- no real graph retrieval yet

### 3.2 Ingest Pipeline Still Minimal
- no entity extraction
- no relation extraction
- no graph-building pipeline beyond placeholder upsert

### 3.3 Retrieval Validation Still Incomplete
- SQLite vector path exists, but still needs explicit closed-loop validation:
  - ingest -> upsert -> search -> query
- current project needs stronger proof that the real vector backend is the active runtime path in integration scenarios

### 3.4 Deployment Hardening
- dockerized real backend composition still incomplete
- production config / persistence / startup flow still needs tightening

---

## 4. Phase Plan

### Phase B: Real Vector Retrieval (COMPLETED ✅)
- real embedding already completed
- SQLiteVectorStore already implemented
- verify SQLite as real runtime retrieval path
- add explicit integration tests for real vector closed loop
- optionally switch SQLite to default local backend after validation

### Phase C: Real GraphRAG
- implement Neo4jGraphStore
- define graph schema
- add graph ingest pipeline
- add real graph retrieval

### Phase D: API Hardening
- integrate real backends end-to-end
- improve validation and failure handling
- add stronger integration testing
- docker deployment and local reproducibility

---

## 5. Day Plan

### Day20
- real embedding integration

### Day21
- SQLiteVectorStore implementation review
- runtime wiring confirmation
- verify that vector store abstraction is already compatible with real backend

### Day22
- validate SQLite runtime path
- validate persistence across app restart
- validate ingest/query closed loop
- establish memory vs sqlite contrast

### Day23
- introduce minimal GraphStore implementation (in-memory)
- design graph schema (node / edge)
- add graph ingest pipeline (basic entity extraction)
- implement graph retrieval
- connect graph retrieval into QueryService

### Day24–25
- Neo4jGraphStore implementation

### Day26–27
- graph ingestion + graph retrieval

### Day28–30
- API hardening + deployment + end-to-end validation

---

## 6. Final Target

Client → FastAPI → Services → Embedding → Vector + Graph → LLM

Target end state:
- real embedding
- real vector retrieval
- real graph retrieval
- observable query pipeline
- deployable local GraphRAG prototype

---

## 7. Interview Summary

This is a Clean Architecture GraphRAG system with:
- full ingest/query pipeline
- hybrid retrieval orchestration
- observability and retrieval timing
- real embedding integration
- real SQLite vector store integration
- pluggable runtime backends
- graph backend still under construction

---

## 8. One Sentence

A partially real GraphRAG system: real embedding and real SQLite vector retrieval are already in place, while graph infrastructure and full end-to-end hardening are still in progress.
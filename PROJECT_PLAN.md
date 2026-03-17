# 🚀 PROJECT_PLAN.md (Detailed v2)

## 0. Project Positioning

This project is an industrial-grade GraphRAG system prototype built with Clean Architecture.

It includes:
- API Layer (FastAPI)
- Application Layer (QueryService / IngestService)
- Domain Models
- Ports (interfaces)
- Infra (Embedding / Vector / Graph / LLM)

⚠️ Current status:
This is NOT a pure skeleton anymore.
It is a partially functional system with API + ingest + query pipelines.

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
- debug info (timings + stats)

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

---

### 1.4 Infra Layer (PARTIAL)

#### Embedding
- SentenceTransformer implemented
- default still uses FakeEmbedding

#### Vector Store
- SQLiteVectorStore implemented
- supports upsert + cosine search

#### Graph Store
- currently InMemoryGraphStore
- NOT real Neo4j yet

---

### 1.5 Testing

- unit tests
- integration tests
- service smoke tests

---

## 2. Reality Check

This system is:

✅ API-ready  
✅ Pipeline-complete  
❌ Not fully production-ready  

---

## 3. Core Gaps

### 3.1 Runtime Wiring
- fake components still used

### 3.2 Graph Missing
- no Neo4j
- no graph schema

### 3.3 Ingest Pipeline
- no entity extraction
- no graph building

---

## 4. Phase Plan

### Phase B: Real Retrieval
- switch embedding to real
- switch vector store to SQLite default

### Phase C: GraphRAG
- implement Neo4jGraphStore
- graph schema
- graph retrieval

### Phase D: API Hardening
- integrate real backends
- validation
- integration testing
- docker deployment

---

## 5. Day Plan

Day20–21:
- real embedding

Day22–23:
- SQLite vector

Day24–25:
- Neo4j graph

Day26–27:
- graph retrieval

Day28–30:
- API hardening + deployment

---

## 6. Final Target

Client → FastAPI → Services → Embedding → Vector + Graph → LLM

---

## 7. Interview Summary

This is a clean-architecture GraphRAG system with:
- full ingest/query pipeline
- hybrid retrieval
- observability
- partial real infra

---

## 8. One Sentence

Half-real GraphRAG system awaiting full backend integration.

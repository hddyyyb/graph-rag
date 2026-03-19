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
❌ Not fully production-ready:
   - graph retrieval is not production-grade
   - no persistent graph backend
   - no multi-hop reasoning
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


### Day23 - GraphRAG Minimal Implementation
- introduce minimal GraphStore implementation (in-memory)
- design graph schema (node / edge)
- add graph ingest pipeline (basic entity extraction)
- implement graph retrieval
- connect graph retrieval into QueryService

#### What was introduced

- InMemoryGraphStore (minimal graph backend)
- Chunk-level graph modeling (ChunkGraphRecord)
- Term-based graph retrieval
- Graph retrieval integrated into QueryService (via enable_graph flag)

#### Data Flow

Ingest:
Document → Chunk → Terms extraction → ChunkGraphRecord → GraphStore

Query:
Query → Terms → GraphStore search → RetrievedChunks → Merge → Answer

#### Current Limitations

- No real entity extraction (rule-based terms only)
- No graph traversal (no multi-hop)
- No advanced ranking (term overlap only)
- No persistent graph backend (in-memory only)

#### Status

Graph is now a first-class retrieval signal (alongside vector).
System upgraded from VectorRAG → GraphRAG (minimal version).

### Day24–25 — Neo4j Graph Backend Implementation

Objective:
Replace InMemoryGraphStore with a real graph database backend (Neo4j), while keeping Application layer unchanged.

Tasks:

- Design Neo4j graph schema:
  - (:Chunk {chunk_id, doc_id, text})
  - (:Term {name})
  - (Chunk)-[:MENTIONS]->(Term)
  - (Term)-[:CO_OCCURS_WITH {weight}]->(Term)

- Implement Neo4jGraphStore:
  - upsert_chunk_graphs(records)
  - search(query, top_k)

- Implement:
  - term-based lookup via Cypher
  - basic scoring (term overlap or frequency)

- Integrate Neo4j driver (bolt/http)

- Extend container:
  - support `graph_store_backend = memory | neo4j`

Constraints:

- Do NOT change:
  - GraphStorePort
  - IngestService / QueryService interfaces

- Do NOT implement:
  - multi-hop traversal
  - advanced ranking

Deliverable:

- Neo4jGraphStore fully working
- Graph backend swappable (memory / neo4j)

---

### Day26 — Neo4j Graph End-to-End Validation

Objective:
Ensure Neo4j backend is fully functional and consistent with existing behavior.

Tasks:

- Write tests:
  - Neo4jGraphStore upsert + search
  - ingest → Neo4j write verification
  - query(enable_graph=True) → Neo4j retrieval

- Cross-backend comparison:
  - memory graph vs neo4j graph (same input → similar output)

- Validate:
  - graph-only retrieval path
  - correctness of scoring and top_k

- Add observability:
  - trace graph_hit_count
  - trace neo4j query timing

Deliverable:

- Verified Neo4j graph retrieval pipeline
- No regression vs InMemoryGraphStore

---

### Day27–28 — Advanced Vector Store Backend

Objective:
Upgrade vector backend from SQLite to a production-grade vector database.

Options (choose ONE):

- Milvus (preferred for industry realism)
- Qdrant (preferred for simplicity and local dev)
- (Optional fallback) FAISS (embedded)

Tasks:

- Implement new VectorStore:
  - upsert(doc_id, chunks, embeddings)
  - search(query_embedding, top_k)

- Integrate backend:
  - docker / local service
  - connection config

- Extend container:
  - `vector_store_backend = memory | sqlite | <new_backend>`

- Ensure compatibility:
  - no changes to QueryService
  - same interface as existing VectorStorePort

Deliverable:

- Real vector database integrated
- Backend switchable without code changes

---

### Day29 — End-to-End System Hardening

Objective:
Stabilize the system for real usage and demos.

Tasks:

- Full pipeline validation:
  - ingest → vector + graph → query → answer

- Edge case handling:
  - empty query
  - no hits
  - backend unavailable

- Error classification:
  - InvalidArgument / Unavailable / Internal

- Config validation:
  - backend selection
  - connection failure handling

- Improve logging & trace:
  - trace_id propagation
  - retrieval timings (vector / graph)

Deliverable:

- Robust, failure-aware system behavior
- Clean observability signals

---

### Day30 — Final Integration & Production-Ready Packaging

Objective:
Prepare the project as a production-grade portfolio system.

Tasks:

- Final E2E test:
  - real embedding + Neo4j + vector DB

- Docker Compose:
  - API + Neo4j + vector DB

- API validation:
  - /ingest
  - /query
  - /health

- Documentation update:
  - architecture overview
  - backend switching
  - system flow diagrams

- README enhancement:
  - GraphRAG explanation
  - design decisions
  - system capabilities

Deliverable:

- Fully runnable system (one-command startup)
- Production-level README
- Interview-ready project
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
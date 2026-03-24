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

### 1.3 Ports Layer (COMPLETED)

The system defines explicit Ports between Application and Infrastructure.

Current ports include:

- EmbeddingProviderPort
  - embed_texts()
  - embed_query()

- VectorStorePort
  - upsert()
  - search()

- GraphStorePort
  - upsert_chunk_graphs()
  - search()

- RetrievalPostProcessorPort
  - process()

- TracePort
  - get_trace_id()
  - set_trace_id()
  - bind()
  - event()

- ClockPort
  - now_iso()

- LLMPort
  - generate()

- RAGKernelPort
  - generate_answer()

Design role of Ports:

- decouple QueryService / IngestService from concrete backends
- keep Application layer independent from SQLite / Neo4j / OpenAI / logging implementations
- support backend swapping without changing application logic
- make runtime wiring explicit in the container

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

- InMemoryGraphStore (baseline implementation)
- Neo4jGraphStore implemented
- supports:
  - chunk-term graph modeling
  - term-based retrieval
  - Cypher-based lookup
- graph backend is now swappable:
  - memory / neo4j
- graph-only retrieval closed loop verified via API integration tests

#### Graph Retrieval (UPDATED — V2)

Graph retrieval has been upgraded from direct term matching to a structure-aware retrieval strategy.

Implemented capabilities:

- 1-hop term expansion over `CO_OCCURS_WITH`
- dual-channel retrieval:
  - direct term hits
  - expanded term hits
- weighted graph scoring:
  - direct hit = 1.0
  - expanded hit = 0.5
- chunk-level aggregation with deduplicated term sets
- consistent behavior across memory / Neo4j backends

⚠️ Current limitations:
- no multi-hop traversal (>1 hop)
- edge weights not used in scoring
- no path-based reasoning
- no entity-level modeling (term-based only)

#### LLM
- fake / local / OpenAI backends can be switched in container
- runtime backend selection pattern is already established
---

### 1.5 Runtime Wiring (STABLE ✅)

- configuration fully unified via Settings
- settings_override is only used at app initialization
- build_container now depends solely on Settings object

- container acts as the single composition root:
  - embedding / vector / graph / llm all constructed inside container
  - no direct dict-based config usage

- backend switching is deterministic:
  - memory / sqlite / neo4j combinations fully supported
  - no code changes required when switching backend

- ingest and query services share the same backend instances:
  - same VectorStore instance
  - same GraphStore instance

- runtime behavior is now testable and validated via wiring tests

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

- configuration system tests added:
  - Settings validation (normalization + cross-field)
  - default config behavior verification

- container wiring tests added:
  - backend selection correctness
  - shared instance verification
  - deterministic runtime behavior

- create_app tests added:
  - settings_override propagation
  - container consistency

Current test status:
- ~90 tests passing
- covers config / container / API / integration layers
---

## 2. Reality Check

This system is:

✅ API-ready  
✅ Pipeline-complete  
✅ Real embedding available  
✅ Real vector store available  
✅ Graph backend now supports Neo4j (real backend)
⚠️ Graph retrieval upgraded to structure-aware (1-hop expansion), but still not production-grade:
   - no multi-hop reasoning
   - no edge-weight-aware scoring
✅ runtime configuration and backend switching now stable and testable
✅ Real vector retrieval closed loop validated with dedicated integration tests
❌ Not fully production-ready:
   - graph retrieval is not production-grade
   - no persistent graph backend
   - no multi-hop reasoning
---

## 3. Core Gaps

### 3.1 Graph Retrieval Not Yet Production-Grade

- Neo4jGraphStore implemented
- graph schema is minimal (Chunk / Term)
- retrieval is term-overlap based

- Graph Retrieval V2 implemented:
  - 1-hop term expansion
  - weighted scoring
- still missing:
  - multi-hop traversal
  - edge-weight-aware ranking
  - path reasoning
  - entity-level graph modeling

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

### Phase C: Real GraphRAG (PARTIALLY COMPLETED)
- Neo4jGraphStore implemented
- graph ingestion pipeline established
- graph-only retrieval validated

Next:

- improve graph scoring
- introduce entity-level modeling
- add multi-hop retrieval

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

### Day24 — Neo4j Graph Backend Implementation (COMPLETED ✅)

- Neo4jGraphStore implemented
- schema defined:
  - Chunk / Term / MENTIONS / CO_OCCURS_WITH
- Cypher-based ingestion and retrieval implemented
- graph backend successfully integrated into container
- graph-only API closed loop validated:
  - /ingest → Neo4j write
  - /query(enable_graph=True) → Neo4j retrieval

---

### Day25 — Configuration Unification & Runtime Stability (COMPLETED ✅)

Objective:
Stabilize runtime configuration and ensure clean backend switching.

Tasks:

- unify all runtime configs into Settings:
  - vector_store_backend
  - graph_store_backend
  - llm_backend
  - sqlite_path
  - neo4j configs

- refactor build_container():
  - remove direct usage of settings_override dict
  - rely only on Settings object

- validate:
  - backend switching via create_app(settings_override)
  - no API layer changes required

- add integration tests:
  - backend switching correctness
  - container consistency

Deliverable:

- clean configuration system
- deterministic runtime behavior
- improved engineering consistency
- unified configuration system (Settings as single source of truth)
- container refactored into clean composition root
- deterministic backend switching verified via tests
- system upgraded from "working" to "engineering-stable"
---

### Day26 — Graph Retrieval V2 Upgrade (COMPLETED ✅)

Objective:
Upgrade graph retrieval from term-level matching to structure-aware retrieval.

Tasks:

- introduce 1-hop term expansion over CO_OCCURS_WITH
- implement dual-channel retrieval:
  - direct term hits
  - expanded term hits
- design graph-aware scoring:
  - direct hit weight = 1.0
  - expanded hit weight = 0.5
- implement chunk-level aggregation and ranking
- unify behavior across:
  - InMemoryGraphStore
  - Neo4jGraphStore

Validation:

- expansion recall test (1-hop reachability)
- direct vs expanded ranking test
- cross-backend consistency verification

Deliverable:

- Graph Retrieval V2 fully implemented
- structure-aware graph retrieval enabled
- test suite extended (96 tests passing)

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


最后，回去优化chunk切分部分


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
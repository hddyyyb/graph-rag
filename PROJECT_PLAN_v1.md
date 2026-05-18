# GraphRAG Project Plan (Industrial-Grade Optimized Version)

---

## 0. Project Positioning

This project is an **industrial-grade GraphRAG system prototype** built with Clean Architecture.

It includes:

- API Layer (FastAPI)
- Application Layer (QueryService / IngestService)
- Domain Models
- Ports (interfaces)
- Infra (Embedding / Vector / Graph / LLM)

### 🎯 Goal

Build a **production-oriented GraphRAG system** that:

- combines vector retrieval and graph retrieval
- improve retrieval quality (recall & ranking accuracy)
- design effective scoring functions for hybrid retrieval
- enable structure-aware reasoning beyond pure vector similarity
- provides full explainability for retrieval results
- supports pluggable backends

---

## 1. System Architecture Overview

### Core Design

1. Hybrid Retrieval (Vector + Graph)
2. Structure-aware Graph Retrieval
3. Explainable Retrieval Pipeline
4. Clean Architecture (decoupled infra)

---

### Retrieval Pipeline

Key idea:
Vector retrieval captures semantic similarity,
while graph retrieval introduces structural signals to improve recall and ranking.

```text
Query
  ↓
Embedding
  ↓
Vector Retrieval
  ↓
Graph Retrieval (1-hop expansion)
  ↓
Fusion (vector + graph)
  ↓
Post-processing
  ↓
LLM Generation
```

---

### Explainability

Each result includes:

```json
{
  "direct_terms": [],
  "expanded_terms": [],
  "direct_score": 1.0,
  "expanded_score": 1.5,
  "final_score": 2.5
}
```

---
### Scoring Design

The retrieval scoring combines semantic similarity and graph signals:

```final_score = α * vector_score + β * graph_score```

Graph score:

```graph_score = direct_hits * w1 + Σ(edge_weight * w2)```

#### Key Insights

- vector retrieval captures semantic similarity
- graph retrieval introduces structural signals
- edge weights reflect strength of term relationships

This design allows:

- enables hybrid retrieval beyond pure embedding similarity
- improves recall via graph expansion
- allows controllable ranking via α / β
- provides a foundation for future learned ranking models

---

## 2. Completed Work (Phase Summary)

---

### Phase 1 — RAG Foundation (Day20–Day22)

#### ✅ Completed

- SentenceTransformer embedding integration
- SQLiteVectorStore (persistent + cosine similarity)
- Full ingest → query pipeline
- FastAPI API:

```text
POST /ingest
POST /query
GET  /health
```

#### 💡 Capability

- End-to-end RAG system (production-style pipeline)

---

### Phase 2 — GraphRAG Introduction (Day23–Day24)

#### ✅ Completed

- InMemoryGraphStore
- Neo4jGraphStore
- Chunk → Term → Graph modeling
- Graph retrieval (term-based)

#### 💡 Capability

- Upgraded RAG → GraphRAG

---

### Phase 3 — Graph Retrieval V2 (Day25–Day27)

#### ✅ Completed

- 1-hop expansion (CO_OCCURS_WITH)
- dual-channel retrieval:
  - direct hits
  - expanded hits
- Graph debug + explainability
- unified Settings + container wiring

#### 💡 Capability

Capability:

- Introduced 1-hop graph expansion to improve recall
- Compared direct vs expanded term contributions
- Designed initial scoring scheme:
  direct_hit = 1.0
  expanded_hit = 0.5

👉 Key improvement:
Graph enables retrieving semantically related chunks not captured by embeddings

---

### Phase 4 — Hybrid Retrieval (Day28)

#### ✅ Completed

- vector + graph fusion
- deduplication by (doc_id, chunk_id)
- unified ranking

```text
final_score = α * vector + β * graph
```

#### 💡 Capability

- Hybrid retrieval system

---

### Phase 5 — Graph Retrieval V3 (Day29)

#### ✅ Completed

- edge-weight-aware scoring
- expansion ranking optimization
- explainable scoring breakdown
- memory vs neo4j alignment

```text
score = direct_count * w1 + Σ(edge_weight * w2)
```

#### 💡 Capability

- Upgraded scoring from count-based → weight-aware
- Introduced edge-weight into scoring function:

score = direct_count * w1 + Σ(edge_weight * w2)

👉 Key improvement:

- stronger semantic relations → higher ranking
- reduced noise from weak expansions
- more fine-grained ranking control

---

## 3. Current System Status

### ✅ Already Achieved

The system has reached a **functional and engineering-stable GraphRAG stage**:

- full ingest → retrieve → generate pipeline
- hybrid retrieval (vector + graph)
- structure-aware graph retrieval with weighted 1-hop expansion
- explainability:
  - retrieval debug
  - scoring breakdown
  - trace_id + timing
- pluggable backend architecture:
  - vector: memory / SQLite
  - graph: memory / Neo4j
  - llm: fake / local / OpenAI
- unified configuration via Settings + container
- deterministic runtime behavior with test coverage

---

### ⚠️ Current Limitations

#### Retrieval Quality

- current graph retrieval is based on:
  - **weighted 1-hop term expansion**
  - scoring driven by edge weights and hit counts

- limitations:
  - no multi-hop traversal (>1 hop)
  - no path-aware reasoning
  - no entity-level modeling (term-based only)

- chunking strategy is still basic:
  - no recursive / semantic chunking
  - limited structural metadata

---

#### Retrieval Evaluation

- no offline benchmark dataset
- no evaluation metrics:
  - Recall@K
  - MRR
- no comparison:
  - vector vs graph vs hybrid

---

#### Infrastructure Limitations

- SQLite vector store is not scalable
- no ANN indexing
- no production-grade vector DB (Milvus / Qdrant)
- no full deployment (Docker Compose)

---

### 🔬 Open Problems

- How to design multi-hop graph reasoning for retrieval?
- How to model entities beyond surface-level terms?
- How to learn optimal scoring weights instead of heuristic tuning?

---

## 4. Next Phase Plan (🔥 Core Upgrade)

---

### Phase 6 — Retrieval Quality Upgrade

---

## Day30–Day31 — Chunking Optimization

- implement multiple chunking strategies:

```text
- fixed-length chunking
- recursive chunking (recommended)
- semantic chunking (optional, not implemented)
```
- introduce Chunker abstraction (ChunkerPort)
- integrate chunker into container
- enable runtime strategy switching via Settings
- extend Chunk metadata (minimal scope only):

```json
{
  "chunk_id": "...",
  "parent_id": "...",
  "position": 0,
  "length": 123,
  "section": null
}
```

- added chunk quality observability:
  - chunk_count
  - min / max / avg length
  - length distribution preview

- added ingest-level tests for chunk quality

---

## Day32 — Multi-format Document Support(Completed)

- introduced DocumentLoader abstraction(`DocumentLoaderPort`, `SimpleDocumentLoader`)
- supported input formats: TXT / PDF / DOCX
- introduced unified ingestion flow:

```text
file → loader → text → chunk → embedding → vector + graph
```

- added `IngestService.ingest_file(...)` entrypoint (reuse existing pipeline)
- integrated with container and test system
- added unit / integration / regression tests (all passed)

⚠️ Scope Boundaries
- text-only PDF (no OCR)
- no table / image parsing
---

## Day33–Day34 — Evaluation Module (🔥 Critical)

### Day33 — Metrics & Framework

- implement metrics:` Recall@K / MRR implemented `
- define evaluation structures: `EvalSample / EvalResult / EvalSummary`
- implement evaluation runner: `evaluate_dataset(mode = vector / graph / hybrid)`

### Day34 — Real Benchmark Validation

- build small real dataset (English)
align: ` query ↔ relevant_chunk_ids `
- run evaluation: `vector / graph / hybrid comparison`
Results:
```text
Vector:
- Recall@3 = 0.50
- MRR = 0.50

Graph:
- Recall@3 = 0.67
- MRR = 0.83

Hybrid:
- Recall@3 = 0.67
- MRR = 0.83
```
Key Findings:
graph retrieval works under proper term extraction
graph outperforms vector on current dataset
hybrid is dominated by graph signal
Chinese failure traced to term extraction mismatch

---
## Day35 — Retrieval Error Analysis (Completed)

### Completed

- extended evaluation with case-level error analysis:
```text
- relevant_chunk_ids
- relevant_ranks
- false_negatives
- false_positives
```
- implemented error analysis logic in `evaluate_sample`
- added dedicated tests (test_error_analysis.py) covering:
```text
- full hit
- partial hit
- full miss
- empty retrieval
```
- added human-readable analysis script:
`src/graph_rag/evaluation/run_case_analysis.py`
- verified on real benchmark dataset

### Key Findings
- Graph retrieval reduces false negatives compared to Vector
- Hybrid results are currently close to Graph (graph-dominated fusion)
- Graph introduces some false positives due to broad term expansion

### Outcome
The system now supports explainable retrieval evaluation at case level,
enabling systematic diagnosis of retrieval failures and guiding future optimization.

---

## Day36-Day37 — Qdrant Vector Database & Docker Infra Upgrade

### Updated Status

- graph_store_backend = memory | neo4j
- vector_store_backend = memory | sqlite | qdrant
- Docker infra unified via docker-compose:
  - Neo4j (Docker)
  - Qdrant (Docker)


### ✅ Day36 — Infra Integration (Completed)

#### Completed

- introduced docker-compose.yml:
```text
- unified Neo4j + Qdrant container management
- replaced manual docker start with docker compose
```
- extended Settings:
```text
vector_store_backend = memory | sqlite | qdrant
qdrant_host / qdrant_port / qdrant_collection_name added
```

- implemented QdrantVectorStore:
```text
- upsert (with doc-level overwrite)
- search (cosine similarity)
- payload: doc_id / chunk_id / text
- deterministic point_id via uuid5
```
- integrated into composition root (main.py):
```text
- lazy import QdrantVectorStore
- no impact on existing backends
```
- added integration test (Docker Qdrant):
```text
- upsert + search works
- retrieval result verified
```
- added file ingestion API:
```text
POST /ingest/file
- UploadFile support
- temp file handling
- reuse IngestService.ingest_file
```

## Day37 — Validation & Positioning

### Tasks

1. Backend Comparison (SQLite vs Qdrant)
- run same queries on sqlite / qdrant
- compare Recall@K / MRR (small dataset)
- analyze latency difference

2. Retrieval Behavior Analysis
- observe vector score distribution
- verify ranking stability
- inspect edge cases (empty results / low similarity)

3. Infrastructure Validation
- verify Qdrant integration correctness
- ensure VectorStore abstraction consistency
- confirm backend switching via Settings

4. Engineering Polishing
- clean test data / collections
- define collection lifecycle strategy (dev / eval / prod)
- ensure reproducible evaluation dataset

5. Documentation Integration
- integrate validation results into infra documentation
- update 49_vector_store_qdrant.md

## Goal

Upgrade from: FastAPI + Neo4j + SQLite

to: FastAPI + Neo4j + Qdrant (Docker-managed, pluggable backend)

with:

- unified infrastructure
- service-based vector retrieval
- production-oriented data management
---

## Day38 — System Understanding (Core) ✅ Completed

### Completed

- traced QueryService.query() end-to-end execution flow
- mapped each pipeline stage to actual code:
  - embedding
  - vector retrieval
  - graph retrieval
  - fusion
  - post-processing
- identified score computation:
  - vector_score → VectorStore
  - graph_score → GraphStore
  - final_score → QueryService._fuse_chunks
- identified merge point:
  - vector + graph results merged in _fuse_chunks
- identified debug injection:
  - retrieval_debug assembled in _build_answer

### Key Understanding

- QueryService is an orchestration layer (no algorithm implementation)
- Graph retrieval performs term expansion based on co-occurrence
- retrieval results depend on both:
  - semantic similarity (vector)
  - structural signals (graph)

### Experiment

- constructed vector-strong vs graph-strong samples
- verified fusion behavior:

```text
alpha=0.5, beta=0.5 → graph-dominant ranking
alpha=1.0, beta=0.1 → vector-dominant ranking
```

### Outcome
- achieved full understanding of retrieval pipeline
- gained ability to control ranking via fusion weights
- upgraded from "system user" → "system controller"

---
## Phase 7 — Retrieval Engineering Refinement

## Day39 — Retrieval Limitation Analysis (Completed)

### Completed

- analyzed fusion behavior under different alpha / beta settings
- compared vector / graph / hybrid retrieval ranking
- inspected retrieval_debug and scoring breakdown
- analyzed false positives and ranking failures
- validated chunk boundary impact on retrieval quality

### Key Findings

1. Chunk granularity strongly affects retrieval quality.
Small chunk sizes can split one semantic unit into multiple chunks, causing false negatives.

2. Global topic chunks dominate retrieval ranking.
Chunks containing high-frequency topic terms such as “Meteor City” are repeatedly ranked above more specific answer chunks.

3. Graph retrieval introduces centrality bias.
High-degree or high-frequency terms tend to dominate graph expansion and scoring.

4. Fusion weight tuning is currently ineffective.
Changing alpha / beta has limited impact because vector_score and graph_score are not normalized to the same scale.

### Root Causes

- vector retrieval focuses on global semantic similarity
- graph retrieval favors highly connected terms
- current fusion directly sums raw scores
- no frequency-aware correction exists

### Future Directions

- TF-IDF / BM25-style term weighting
- score normalization before fusion
- graph centrality penalty
- reranking after retrieval
- future multi-hop graph reasoning

---

## Day40 — Fusion Score Normalization ✅ Completed

### Completed

- implemented optional min-max normalization inside fusion logic
- normalized vector_score and graph_score before fusion
- added normalization debug fields:
  - normalization_enabled
  - normalization_method
  - raw_vector_score
  - raw_graph_score
- preserved backward compatibility
- added minimal fusion normalization tests

### Validation

- verified normalized score range: [0, 1]
- verified alpha / beta can affect ranking under controlled samples
- reduced raw score scale imbalance between vector and graph retrieval

### Constraints Kept

- no vector store modification
- no graph store modification
- no new dependencies
- changes localized to QueryService fusion logic

---

## Day41 — Retrieval Scoring Improvement ✅ Completed

### Completed

- analyzed graph centrality bias and noisy expansion behavior
- inspected retrieval_debug scoring breakdown
- implemented minimal graph score constraint:
  - expansion contribution cap
- updated graph scoring:

```text
score = direct_score + min(expanded_score, expansion_score_cap)
```

- added scoring debug fields:
  - capped_expanded_score
  - expansion_score_cap
  - expansion_capped

### Validation

- verified before / after retrieval behavior
- reduced noisy graph expansion domination
- validated InMemory / Neo4j consistency
- added regression tests

### Constraints Kept
- no architecture redesign
- no retrieval pipeline refactor
- no reranker
- no multi-hop graph
- no external search library

---

## Day42 — Retrieval Debugging & Observability ✅ Completed

### Completed

- organized retrieval debugging workflow
- improved retrieval_debug readability with structured sections:
  - summary
  - ranking_preview
  - scoring_overview
  - fused
  - final
- clarified retrieval result stages:
  - vector_chunks / graph_chunks: raw retrieval results
  - fused_chunks: fusion output before post-processing
  - final_chunks: post-processed final results
- replaced ambiguous `merged` debug naming with `final`
- added ranking_preview based on final_chunks
- enriched ranking_preview with:
  - vector_hit / graph_hit
  - raw_vector_score / raw_graph_score
  - effective_vector_score / effective_graph_score
  - final_score
- added scoring_overview for:
  - alpha / beta
  - normalization status
  - graph scoring weights
  - expansion_score_cap
  - expansion capped status
- added retrieval_query_done structured trace event
- connected enable_fusion_score_normalization from Settings to QueryService through API container initialization
- updated scripts README and retrieval debugging workflow documentation
- verified real logging output includes normalization status
- passed pytest -q

### Key Outcome

The retrieval pipeline now has a clearer observability layer.

Developers can inspect retrieval behavior from three levels:

1. runtime logs for quick diagnosis
2. retrieval_debug for structured result analysis
3. debugging scripts for deep graph / fusion inspection

### Validation

- pytest -q passed
- inspect_graph_scoring_case.py verified debug output
- real logging verified:
  - query_done uses final
  - retrieval_query_done includes normalization_enabled=True
  - retrieval_query_done includes mode, counts, top1 result, and scoring configuration

### Constraints Kept

- no retrieval pipeline redesign
- no reranker
- no new infrastructure
- no architecture change

---

## Goal

- improve retrieval observability
- make ranking behavior easier to analyze
- strengthen debugging-oriented engineering skills

---

## Day43 — Engineering Quality Improvement

### Tasks

- review Settings structure and retrieval config naming
- organize retrieval-related configs:
  - vector_top_k
  - graph_top_k
  - fusion_alpha
  - fusion_beta
  - enable_fusion_score_normalization
- consider adding `.env.example`
- improve exception handling
- reduce hardcoded parameters
- improve code readability and consistency
- clean temporary debugging logic if necessary
- review logging field naming consistency
- improve maintainability of retrieval pipeline code

### Constraints

- avoid business logic redesign
- avoid large refactors
- do not change retrieval scoring logic
- focus on maintainability and code quality

---

## Goal

- improve engineering quality
- strengthen production-oriented coding habits
- improve long-term maintainability of the project
---

## Phase 8 — Advanced Retrieval Exploration (Optional)

## Day44 — Retrieval Refactoring

### Tasks

- review QueryService complexity
- improve helper method boundaries
- simplify retrieval-related flow if needed
- improve internal naming consistency
- reduce coupling between retrieval stages

---

## Goal

- improve code structure readability
- strengthen safe refactoring ability
- practice incremental engineering optimization

---

## Day45 — Future Retrieval Directions

### Tasks

- explore reranking directions
- explore future multi-hop graph retrieval
- analyze retrieval scalability limitations
- investigate hybrid retrieval tradeoffs
- summarize long-term retrieval roadmap

---

## Goal

- transition from feature implementation
  → retrieval system design thinking
- strengthen long-term retrieval engineering understanding

---

## 5. Final Target Architecture

```text
Client
  ↓
FastAPI
  ↓
QueryService / IngestService
  ↓
Embedding
  ↓
Vector DB + Graph DB
  ↓
LLM
```

---

## 6. Interview Positioning

This project demonstrates:

- Clean Architecture design
- hybrid retrieval system
- graph-based reasoning
- explainable AI system
- pluggable backend design
- production-oriented engineering

---

## 7. One Sentence Summary

A production-oriented GraphRAG system with hybrid retrieval, explainability, and pluggable infrastructure, upgraded from heuristic retrieval to structure-aware reasoning.

---
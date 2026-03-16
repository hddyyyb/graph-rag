# Production-Oriented GraphRAG Project Plan

## 1. Project Status Rebaseline

This project is currently in a **mid-stage architecture-first state**.

### Already completed
- Clean Architecture style project skeleton is established
- Domain / Application / Ports / Infra boundaries are defined
- QueryService main workflow has been built
- RetrievalPostProcessor supports sorting, deduplication, top_k, min_score, and citations
- QueryOptions normalization and application-layer parameter flow are in place
- QueryService observability structure has been partially introduced
- Error boundary handling and failure semantics have been improved
- Unit tests currently pass based on fake implementations

### Not yet truly implemented
- Real EmbeddingProvider implementation
- Real VectorStore implementation
- Real GraphStore implementation
- Real indexing pipeline for document ingestion
- Real API delivery path based on actual retrieval backends

### Important clarification
The current project is **not yet a fully working GraphRAG system**.
It is more accurately an **enterprise-oriented application skeleton with testable interfaces and application semantics**.

---

## 2. Core Strategy Adjustment

The previous route spent too much time polishing the application layer before the lower-level retrieval backends were fully implemented.

From this point onward, the priority changes to:

1. implement real backends
2. complete indexing/data flow
3. expose API
4. finalize deployment and project packaging

This means the next phase should focus on turning fake ports into real working modules.

---

## 3. Revised Project Phases

---

### Phase A. Architecture Skeleton and Application Layer
**Status: mostly completed**

Main work:
- project structure
- domain models
- ports and adapters boundaries
- QueryService workflow
- RetrievalPostProcessor
- QueryOptions
- basic observability events
- application-level error boundaries
- fake-driven tests

Goal:
- make the system replaceable, testable, and extensible

---

### Phase B. Real Backend Implementation
**Estimated duration: 7 days**
**Top priority**

Main work:
- implement a real EmbeddingProvider
- implement a real VectorStore
- implement a real GraphStore

Target:
- remove fake core retrieval dependencies
- make hybrid retrieval actually executable

Deliverables:
- real embedding generation
- real vector retrieval
- real graph retrieval
- backend integration tests

---

### Phase C. Indexing and Data Flow Closure
**Estimated duration: 5 days**

Main work:
- document loading
- chunking
- embedding generation pipeline
- vector indexing
- graph construction
- offline indexing script

Target:
- establish a full offline-to-online data loop

Pipeline target:
raw documents -> chunks -> embeddings -> vector store -> graph store -> query

Deliverables:
- indexing script
- sample dataset
- reproducible ingestion flow

---

### Phase D. API and Engineering Integration
**Estimated duration: 5 days**

Main work:
- dependency injection
- composition root
- FastAPI endpoint
- config system
- logging integration
- API-level error mapping

Target:
- expose the GraphRAG system as an actual service

Deliverables:
- runnable API server
- `/query` endpoint
- structured response with answer, citations, trace_id, retrieval_debug

---

### Phase E. Delivery and Resume Packaging
**Estimated duration: 4 days**

Main work:
- Dockerization
- README rewrite
- architecture diagram
- usage examples
- benchmark/demo case
- GitHub cleanup

Target:
- convert the project into a portfolio-grade deliverable

Deliverables:
- polished repository
- deployment instructions
- project highlights for resume/interview use

---

## 4. Revised Daily Sequence

### Day19
Project rebaseline and roadmap rewrite

### Day20-Day26
Phase B: real backend implementation
- embedding
- vector store
- graph store

### Day27-Day31
Phase C: indexing and ingestion pipeline

### Day32-Day36
Phase D: API and engineering integration

### Day37-Day40
Phase E: delivery, packaging, and presentation

---

## 5. Current Execution Rule

Before adding more observability polish or further application-layer refinement, priority must be given to:

- real EmbeddingProvider
- real VectorStore
- real GraphStore

Application-layer refinement should continue only after the lower-level retrieval stack becomes real.

---

## 6. Engineering Principle for This Project

This project should be built according to the following order:

1. architecture boundaries
2. real backend capability
3. data flow closure
4. service exposure
5. deployment and portfolio polish

Avoid over-polishing fake implementations.
Prefer minimal but real working capability over elegant but non-executable abstractions.

---

## 7. End Goal

This project aims to become a **production-oriented GraphRAG engineering project** suitable for:
- AI engineering job applications
- RAG system portfolio presentation
- future extension toward enterprise document QA systems

The final project should demonstrate:
- clean architecture
- replaceable retrieval components
- hybrid retrieval
- observability
- API service capability
- deployment readiness
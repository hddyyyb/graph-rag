# 🚀 Production-Oriented GraphRAG System

> A clean-architecture GraphRAG system with hybrid retrieval (vector + graph), full ingest/query pipeline, and observability.

---

## ✨ Overview

This project implements a **production-oriented GraphRAG system** designed with **Clean Architecture** principles.

It is not just a demo — but a **modular, extensible, and observable AI system** that simulates real-world backend engineering for LLM applications.

---

## 🧠 Key Features

- 🔹 **Hybrid Retrieval**
  - Vector similarity search
  - Graph-based retrieval (entity-level matching)

- 🔹 **Full Pipeline**
  - Ingest: document → chunk → embedding → storage
  - Query: query → embedding → retrieval → post-process → LLM answer

- 🔹 **Clean Architecture**
  - Domain / Application / Ports / Infra / API
  - Fully decoupled components

- 🔹 **Pluggable Components**
  - Embedding models (SentenceTransformer / OpenAI / etc.)
  - Vector stores (SQLite / Milvus-ready)
  - Graph stores (InMemory → Neo4j-ready)
  - LLM backends

- 🔹 **Observability**
  - Stage-level latency tracking:
    - embedding_time
    - retrieval_time
    - postprocess_time
    - generation_time
  - Trace ID propagation

- 🔹 **Engineering-Grade Design**
  - Error boundaries
  - Dependency injection
  - Testable services
  - Integration tests

---

## 🏗️ Architecture

```
Client
↓
FastAPI (API Layer)
↓
Application Layer
├── QueryService
└── IngestService
↓
Ports (Interfaces)
↓
Infra Layer
├── EmbeddingProvider
├── VectorStore
├── GraphStore
└── RAGKernel (LLM)
```

---

## 🔄 Data Flow

### Ingest Pipeline

```markdown
Document
→ Chunking
→ Embedding
→ Vector Store
→ Graph Store
```

### Query Pipeline

```markdown
Query
→ Embedding
→ Hybrid Retrieval (Vector + Graph)
→ Post-processing
→ LLM Answer Generation
```

---

## ⚙️ Tech Stack

- Python 3.10+
- FastAPI
- SentenceTransformers
- SQLite (Vector Store)
- (Planned) Neo4j (Graph Store)
- Pytest

---
## 🚦 Current Status

This project is a **partially real GraphRAG system**:

| Component        | Status                  |
|-----------------|-------------------------|
| API             | ✅ Implemented           |
| Ingest Pipeline | ✅ Implemented           |
| Query Pipeline  | ✅ Implemented           |
| Embedding       | ✅ Real (SentenceTransformer) |
| Vector Store    | ✅ SQLite                |
| Graph Store     | ⚠️ InMemory (Neo4j planned) |
| Full Production | ❌ Not yet              |


### Graph Retrieval (NEW)

The system now supports a minimal GraphRAG capability:

- Builds a lightweight graph during ingestion (term co-occurrence)
- Enables graph-based retrieval via keyword matching
- Can be toggled via `enable_graph=True`

This is an initial step toward full GraphRAG support (Neo4j, multi-hop reasoning planned).

---

## 🧩 Design Philosophy

- Build **real systems**, not demos
- Prioritize **modularity and replaceability**
- Separate **business logic from infrastructure**
- Design for **scalability from day one**

---


## 🚀 Getting Started

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Run Services

```bash
docker compose up -d
```

### 3. Start API

```bash
docker start neo4j-local
uvicorn graph_rag.api.main:app --reload --port 8000
```

### 4. Open Docs

```bash

http://localhost:8000/docs
```

---

## 📡 API Endpoints

- `POST /ingest` — ingest documents

- `POST /query` — query system

- `GET /health` — health check

---

## 🧪 Testing

```bash
pytest -q
```
---

## 🧭 Roadmap

- [ ] Replace InMemoryGraphStore with Neo4j
- [ ] Introduce entity extraction for graph building
- [ ] Integrate Milvus / FAISS for scalable vector search
- [ ] Add streaming LLM responses
- [ ] Production deployment (Docker + CI/CD)

---
## 💬 Interview Highlights

- This project demonstrates:
- System design for LLM applications
- Clean Architecture in AI systems
- Hybrid retrieval (vector + graph)
- Observability in ML pipelines
- Real-world backend engineering skills

---

## 📌 One-Line Summary

A **half-real, production-oriented GraphRAG system** designed for extensibility and real backend integration.

---


## 👤 Author

Zhang Yun
PhD in AI | Focus on LLM Optimization & Graph Data Mining


# 🚀 Enterprise GraphRAG System (Production-Oriented)

> A production-oriented GraphRAG system with hybrid retrieval (vector + graph), explainable scoring, and clean architecture design.

---

## 🧠 What This Project Solves

Traditional RAG systems rely purely on vector similarity, which suffers from:

- lack of structural reasoning  
- weak explainability  
- unstable retrieval quality  

This project introduces a Graph-enhanced RAG system (GraphRAG) to address these issues.

---

## 🔥 Key Highlights

### 1️⃣ Hybrid Retrieval (Core Innovation)

- Vector retrieval → semantic similarity  
- Graph retrieval → structural expansion  
- Fusion → unified candidate ranking  

```text
final_score = α * vector_score + β * graph_score
```
---

### 2️⃣ Graph Retrieval V3 (Edge-Aware)

- 1-hop term expansion (CO_OCCURS_WITH)
- Edge-weight-aware scoring
- Structured expansion signals:

```JSON
{
  "query_term": "llm",
  "expanded_term": "rag",
  "weight": 3.0
}
```
---
### 3️⃣ Explainable Retrieval (🔥 Key Feature)

Each result is fully explainable:

- direct_terms
- expanded_terms
- expanded_hits (with contribution)
- direct_score / expanded_score / final_score

👉 You can trace exactly why a chunk is retrieved

---

### 4️⃣ Clean Architecture (Engineering Focus)
```API → Application → Ports → Infra```
- QueryService / IngestService fully decoupled
- Backend swap without changing business logic
- Composition Root (container)

---

### 5️⃣ Dual Backend Support
- Vector:
  - SQLite (implemented)
- Graph:
  - InMemory / Neo4j (implemented)

---

## 🏗️ System Architecture

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

### 🔄 Retrieval Pipeline
```
Query
→ Embedding
→ Vector Retrieval
→ Graph Retrieval (Expansion + Scoring)
→ Fusion
→ Postprocess
→ Answer Generation
```
---

## ⚙️ Tech Stack

- FastAPI
- SentenceTransformers
- SQLite
- Neo4j
- Pytest

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
docker start neo4j-local  # tmp method to start Neo4j container
# http://localhost:6333/dashboard
# http://localhost:8000/docs

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
## 💬 Interview Highlights

This project demonstrates:
- how to design a production-grade RAG system
- how to integrate graph-based retrieval
- how to build explainable retrieval pipelines
- how to apply Clean Architecture in AI systems

---

## 📌 One-Line Summary

A production-oriented GraphRAG system with hybrid retrieval and explainable scoring.

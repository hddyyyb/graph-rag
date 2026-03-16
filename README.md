# Production-Oriented GraphRAG

A production-oriented GraphRAG system built with Clean Architecture.

The goal of this project is to build a modular Retrieval-Augmented Generation (RAG) pipeline supporting hybrid retrieval strategies.

This project focuses on system architecture and engineering design, rather than model optimization.

            +----------------+
            |   User Query   |
            +----------------+
                    |
                    v
            +----------------+
            |  Embedding     |
            +----------------+
                    |
            +-------+-------+
            |               |
            v               v
    Vector Retrieval   Graph Retrieval
            |               |
            +-------+-------+
                    |
            Retrieval PostProcessor
                    |
                    v
            LLM Generation
                    |
                    v
                Answer

## System Architecture

The GraphRAG pipeline:
```
User Query
↓
Embedding
↓
Hybrid Retrieval
├─ Vector Retrieval
└─ Graph Retrieval
↓
Retrieval Post Processing
↓
LLM Generation
```

The system follows Clean Architecture:
```
Domain
Application
Ports
Infrastructure
API
```

More details:
```
docs/architecture.md
```

## Key Features

• Clean Architecture design  
• Hybrid retrieval (Vector + Graph)  
• Modular backend adapters  
• Retrieval observability  
• Extensible indexing pipeline  


## Quick Start (Local)
1) Create virtual environment
```
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2) Start dependencies (Neo4j+Milvus)
```
cp .env.example .env
docker compose up -d
```
3) Start API
```
uvicorn graph_rag.api.main:app --reload --port 8000
```
Run tests: 
```
pytest -q
pytest -q -s
```

4) Access API
- http://localhost:8000/docs

## API
- POST /ingest
- POST /query
- GET /health

## Project Constraints

This project focuses on system architecture and engineering abstraction.

The following topics are intentionally out of scope:

• Algorithm optimization

• Prompt tuning

• Model performance improvement

The goal is to build a production-oriented GraphRAG system architecture.




## Documentation
System documentation is located in:
```
docs/
   architecture.md
   retrieval_design.md
   indexing_pipeline.md
   api_design.md
   observability.md
```


## Development Plan
Project roadmap:
```
PROJECT_PLAN.md
```

Development phases:
```
Phase A  Architecture Skeleton
Phase B  Retrieval Backends
Phase C  Indexing Pipeline
Phase D  API Service
Phase E  Production Packaging
```
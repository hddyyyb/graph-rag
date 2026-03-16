# Project Goal

## One-sentence Goal
Build a production-oriented GraphRAG system supporting:

- Vector retrieval
- Graph retrieval
- Hybrid retrieval
- FastAPI service
- Docker deployment

## Engineering Goals
The system emphasizes engineering quality rather than model performance.

Key engineering goals:

• Deployable system (Docker Compose)  
• Clean architecture  
• Replaceable components  
• Observability  
• Testability 

## Out-of-Scope

The following topics are intentionally excluded:

- Algorithm optimization
- Prompt tuning
- Model performance improvements
- Multi-tenant architecture
- Complex orchestration (K8s/HPA)


## Day30 Acceptance Criteria

The project is considered complete when:

- `/ingest`, `/query`, `/health` APIs are available
- Hybrid retrieval works
- System can be deployed with Docker Compose
- Core modules are replaceable
- Basic observability is available
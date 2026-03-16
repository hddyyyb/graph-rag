# System Architecture

This document describes the system architecture of the GraphRAG system.

The system is designed with **Clean Architecture principles**, ensuring
that core business logic remains independent from infrastructure
implementations.


# 1 Architecture Overview

The GraphRAG system processes a user query through the following
pipeline:

```markdown
User Query
↓
Embedding Generation
↓
Hybrid Retrieval

  ├── Vector Retrieval
  └── Graph Retrieval

↓
Retrieval Post Processing
↓
LLM Generation
↓
Answer + Citations
```

The system supports three retrieval modes:

-   vector_only
-   graph_only
-   hybrid

# 2 Clean Architecture

The system follows a layered architecture:

```markdown
API Layer
↓
Application Layer
↓
Domain Layer
↓
Ports (Interfaces)
↓
Infrastructure (Adapters)
↓
External Services
```

Dependency rule:

API → Application → Domain → Ports\
Infrastructure → Ports

The Application and Domain layers **must not depend on concrete
implementations**.

This ensures that storage engines, embedding models, and LLM providers
can be replaced without modifying business logic.


# 3 Core Modules

## API Layer

Responsibilities:

-   HTTP request handling
-   input validation
-   trace_id generation
-   response formatting

Example endpoints:

```python
POST /ingest\
POST /query\
GET /health
```

Framework:

```python
FastAPI
```

## Application Layer

Contains the main business use cases.

### IngestService

Responsible for document ingestion:
```
document
↓
chunking
↓
embedding
↓
vector store
↓
graph store
```
### QueryService

Responsible for handling queries:

```python
query
↓
embedding
↓
retrieval
↓
post processing
↓
LLM generation
```

## Domain Layer

Defines core domain models.

Key entities:

```python
Document
Chunk
RetrievalResult
Answer
```

The Domain layer contains **no infrastructure dependencies**.


## Ports Layer

Defines abstract interfaces.

Example ports:

```python
EmbeddingProvider
VectorStore
GraphStore
Kernel
Observability
```

The Application layer interacts only with these interfaces.


## Infrastructure Layer

Provides concrete implementations of ports.

Examples:

```python
MilvusVectorStoreAdapter
Neo4jGraphStoreAdapter
OpenAIEmbeddingProvider
LlamaIndexKernelAdapter
```

These adapters translate system operations into calls to external
services.


# 4 Data Storage Design

## Vector Store

Vector database: Milvus

Collection: chunks

Fields:

```python
chunk_id
doc_id
vector
text
metadata
```

Purpose:

-   semantic retrieval
-   top-k similarity search


## Graph Store

Graph database: Neo4j

Node types:

(:Document)\
(:Chunk)\
(:Entity)

Relationships:

(:Document)-\[:HAS_CHUNK\]-\>(:Chunk)\
(:Chunk)-\[:MENTIONS\]-\>(:Entity)

Graph retrieval expands context beyond vector similarity.


# 5 Deployment Architecture

The system is deployed using **Docker Compose**.

Components:

api container\
neo4j container\
milvus container

Environment configuration is provided through `.env` files.



# 6 Extensibility

The architecture allows replacing major components without modifying
business logic.

Replaceable modules:

EmbeddingProvider\
VectorStore\
GraphStore\
Kernel

Examples:

Milvus → FAISS\
Neo4j → ArangoDB\
OpenAI → Local Embedding Model\
LlamaIndex → Custom Kernel

------------------------------------------------------------------------

# 7 Design Principles

Key principles guiding this architecture:

### Separation of Concerns

Each layer has a single responsibility.

### Dependency Inversion

Business logic depends on abstractions, not implementations.

### Replaceable Infrastructure

External services are accessed through adapters.

### Observability

Each request generates a `trace_id` and logs key timing metrics.


# 8 Future Architecture Extensions

Potential future improvements:

-   distributed indexing pipeline
-   retrieval reranking layer
-   streaming query processing
-   additional vector store backends
-   advanced graph reasoning

# Qdrant Vector Store Integration

## Overview

Qdrant is integrated as a pluggable vector database backend in the GraphRAG system.

It replaces the SQLite-based vector store for scalable vector similarity search, while keeping the overall system architecture unchanged.

The integration is implemented via the VectorStorePort abstraction, so QueryService and IngestService do not depend on the underlying storage.

---

## Architecture

IngestService  
→ EmbeddingProvider  
→ QdrantVectorStore  
→ Qdrant (Docker)

QueryService  
→ QdrantVectorStore  
→ RetrievedChunk

---

## Data Model

Each text chunk is stored as a Qdrant point.

A point contains:

- id: generated from doc_id and chunk_id  
- vector: embedding of the chunk  
- payload:
  - doc_id  
  - chunk_id  
  - text  

This allows the system to reconstruct retrieval results without accessing other storage layers.

---

## Core Concepts

collection  
A collection is similar to a table in a database. It stores all vectors.

point  
A single record in Qdrant. Each chunk corresponds to one point.

vector  
The embedding representation of a chunk.

payload  
Metadata stored together with the vector, used for filtering and reconstruction.

cosine similarity  
Used as the distance metric for vector search.

---

## Key Design Decisions

### Deterministic Point ID

The point id is generated using doc_id and chunk_id.  
This ensures that re-ingesting the same document overwrites existing data instead of creating duplicates.

### Payload Storage

The system stores doc_id, chunk_id, and text in payload.  
This allows direct reconstruction of RetrievedChunk during search.

### Lazy Collection Creation

The collection is created on the first upsert.  
Vector dimension is inferred from the embedding size.  
Distance metric is cosine similarity.

### Backend Abstraction

QdrantVectorStore implements the same interface as other vector stores.  
Switching between memory, sqlite, and qdrant requires only configuration changes.

---

## Ingest Flow

Text or file is ingested through API.

The pipeline is:

file or text  
→ loader  
→ chunker  
→ embedding  
→ QdrantVectorStore.upsert  

Each chunk is converted into a vector and stored in Qdrant.

---

## Query Flow

User sends a query.

The pipeline is:

query  
→ embedding  
→ QdrantVectorStore.search  
→ RetrievedChunk  
→ fusion and post-processing  

Qdrant returns top_k most similar vectors based on cosine similarity.

---

## Filtering and Search Options

The system supports:

- filter by doc_id  
- minimum score threshold  

These options are converted into Qdrant filter conditions.

---

## Docker Setup

Qdrant runs as a Docker service.

The system connects via:

- host: localhost  
- port: 6333 or 6334  

Docker Compose is used to manage both Neo4j and Qdrant.

---

## Why Qdrant

### SQLite

- no native vector index  
- poor scalability  
- not optimized for similarity search  

### Qdrant

- designed for vector retrieval  
- supports filtering  
- supports ANN indexing  
- production-ready  

---

## Limitations

Current implementation:

- only supports cosine similarity  
- no ANN tuning  
- no hybrid vector + metadata ranking  
- no batching optimization  

---

## Future Work

- Milvus integration  
- advanced indexing configuration  
- hybrid retrieval optimization  
- performance benchmarking  
- distributed deployment  

## Validation & Engineering Notes (Day37)

### Backend Comparison (SQLite vs Qdrant)

Both backends were evaluated using the same dataset and evaluation samples.

Result:

```text
SQLite:
Recall@3 = 1.0000
MRR = 1.0000
Latency ≈ 25ms

Qdrant:
Recall@3 = 1.0000
MRR = 1.0000
Latency ≈ 38ms
```

Observation:

- Retrieval quality is identical on small datasets.
- Qdrant has slightly higher latency due to service-based architecture.
- Differences will appear at larger scale (ANN vs brute-force).

---

### Retrieval Behavior

Observations:

- top_k results are stable across repeated runs
- relevant queries rank correct chunks at top1
- score shows clear separation between relevant and irrelevant results
- unrelated queries still return top_k results with low or negative scores

Implication:

- post-processing may require min_score filtering

### Engineering Issues

#### Chunk ID mismatch

Evaluation samples must match actual chunk ID format:

```text
{doc_id}#0
```

#### Vector Dimension Mismatch

Qdrant enforces fixed vector dimension:

- sentence-transformer: 384
- hash embedding: 32

Mismatch leads to insertion failure.

#### Collection pollution

Old data remained in collection caused unexpected results.

Solution:

- use isolated collection for evaluation
- reset collection before experiments

### Collection Management Strategy

Qdrant collections are persistent and must be managed explicitly.

Recommended:

```text
dev:
  graphrag_dev

eval:
  graphrag_eval (reset before evaluation)

prod:
  graphrag_prod (doc-level overwrite)
```
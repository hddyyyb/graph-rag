# Application Layer Data Flow

## 1. Ingest Flow

### Input
A document enters the system as:

- `doc_id`
- `text`
- optional `metadata`

### Processing
`IngestService` performs:

1. input validation
2. text chunking
3. chunk embedding
4. vector store write
5. term extraction
6. graph record construction
7. graph store write

### Output
Returns `IngestResult`.

---

## 2. Query Flow

### Input
A query enters the system as:

- `query`
- `QueryOptions` or equivalent overrides

### Processing
`QueryService` performs:

1. options normalization
2. query validation
3. query embedding
4. vector retrieval
5. graph retrieval
6. candidate fusion
7. post-processing
8. answer generation
9. response assembly

### Output
Returns `Answer`.

---

## 3. Important Intermediate Objects

### `QueryOptions`
Represents per-query retrieval settings.

### `RetrievedChunk`
Represents a retrieved chunk candidate with at least:

- doc_id
- chunk_id
- text
- score
- source

### `ChunkGraphRecord`
Represents chunk-level graph ingest data with:

- chunk_id
- doc_id
- text
- terms

### `Answer`
Final query result object containing:

- answer
- trace_id
- retrieval_debug
- citations

---

## 4. Application Layer as Coordinator

The application layer does not own storage and model logic directly.

Instead, it coordinates data as it moves across:

- embedding provider
- vector store
- graph store
- post-processor
- kernel

This is why the application layer is the “system workflow layer” of the project.
# IngestService

## 1. Purpose

`IngestService` is the application-level orchestrator for document ingest.

Its job is to transform a raw document into two retrieval signals:

1. vector-store data
2. graph-store data

This service does not implement embedding, vector storage, or graph storage by itself.  
It coordinates those responsibilities through Ports.

---

## 2. Main Workflow

The ingest pipeline is:

```text
Document
→ Validate input
→ Chunk text
→ Embed chunks
→ Write vector store
→ Extract terms
→ Build ChunkGraphRecord
→ Write graph store
``` 

---

## 3. `_chunk_text(text, chunk_size, overlap)`

### Purpose
Split raw text into overlapping chunks.

### Input

- `text: str`
- `chunk_size: int`
- `overlap: int`

### Output

- `List[str]`

### Behavior

- trims input text
- returns empty list if text is empty
- if `chunk_size <= 0`, returns the whole text as a single chunk
- otherwise slices text with overlap

### Notes

Chunking here is intentionally simple.  
It is a lightweight application-layer utility, not a semantic chunking strategy.

---

## 4. Class: `IngestService`

## 4.1 Responsibility

`IngestService` controls the full ingest workflow.

It is responsible for:

- validating ingest input
- chunking document text
- generating embeddings
- writing vector data
- constructing graph records
- writing graph data
- emitting trace events

---

## 4.2 Constructor Dependencies

### `vector_store: VectorStorePort`
Used to persist chunk embeddings into the vector backend.

### `graph_store: GraphStorePort`
Used to persist chunk-term graph records into the graph backend.

### `embedder: EmbeddingProviderPort`
Used to generate embeddings for all chunks.

### `trace: TracePort`
Used to record ingest lifecycle events and bind trace context.

### `chunk_size: int = 400`
Default chunk size.

### `chunk_overlap: int = 50`
Default overlap size between adjacent chunks.

---

## 4.3 Stored Fields

The class stores:

- `self.vector_store`
- `self.graph_store`
- `self.embedder`
- `self.trace`
- `self.chunk_size`
- `self.chunk_overlap`

These fields define both the service dependencies and the ingest chunking policy.

---

## 5. Method: `ingest(...)`

```python
ingest(
    *,
    doc_id: str,
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> IngestResult
```
### Purpose

Execute a full ingest request.

### Input
- ```doc_id: str```
    - unique logical document identifier
- ```text: str```
    - raw document text
- ```metadata: Optional[Dict[str, Any]]```
    - optional metadata payload
    - currently accepted but not used in the shown implementation

### Output

Returns ```IngestResult```.

Expected semantic content:

- ```doc_id```
- number of chunks written
### Validation Rules
- ```doc_id``` must not be empty
- ```text``` must not be empty
- chunking result must not be empty

Invalid input raises ```ValidationError```.

---

# 6. Internal Execution Steps
## Step 1: Normalize and validate input

The service trims ```doc_id``` and ```text```, then rejects empty values.

## Step 2: Chunk text

Calls ```_chunk_text(...)``` with configured chunk size and overlap.

## Step 3: Bind trace context

Binds ```doc_id``` into the trace context and emits ```ingest_start```.

## Step 4: Generate embeddings

Calls:
```python
self.embedder.embed_texts(chunks)
```
## Step 5: Write vector store
Calls:
```python
self.vector_store.upsert(doc_id, chunks, embeddings)
```
## Step 6: Build graph records

For each chunk:
- generate ```chunk_id``` as ```"{doc_id}#{idx}"```
- extract terms via ```extract_terms(chunk_text)```
- build ```ChunkGraphRecord```
## Step 7: Write graph store

Calls:
```python
self.graph_store.upsert_chunk_graphs(graph_records)
```
## Step 8: Finish trace

Emits ```ingest_done``` and returns IngestResult.

---

# 7. Graph Record Structure

Each chunk is converted into a ```ChunkGraphRecord``` with:

- `chunk_id`
- `doc_id`
- `text`
- `terms`

This is the bridge from raw chunk text into the graph retrieval pipeline.

---

# 8. Error Behavior

This service explicitly raises ```ValidationError``` when:

- ```doc_id``` is empty
- ```text``` is empty
- chunk list is empty after chunking

The current implementation does not wrap downstream infra errors inside a custom ingest-stage exception in this file.
Any backend failure from embedding/vector/graph layers will propagate upward.

---

# 9. Observability

The service emits trace signals through ```TracePort```.

Current events include:

- ```ingest_start```
- ```ingest_done```

Trace binding includes:

- ```doc_id```

This gives basic visibility into the ingest lifecycle.

# 10. Design Notes
## Why chunk before embedding?

Embedding is defined at chunk granularity, not full-document granularity.

## Why write vector first and graph second?

Graph and vector are both derived from chunks and technically independent, but vector indexing is the primary retrieval backbone, while graph is an enhancement layer. So in practice we prioritize vector first to ensure system availability and then build graph as a secondary signal.

In fact, vector and graph can be executed in parallel, but we usually treat vector as the critical path and graph as an asynchronous enrichment process.

# Why is chunk ID derived from document ID + index?

It guarantees deterministic chunk identity within a document.

# 11. Suggested Future Extensions

Potential future improvements:

- metadata persistence
- semantic chunking
- document parser integration (PDF / Word / HTML)
- ingest failure classification
- ingest timings in debug output
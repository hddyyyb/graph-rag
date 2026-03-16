# System Flows

This document describes the main runtime flows of the GraphRAG system, including **document ingestion** and **query processing**.

---

# 1. Ingestion Flow

## 1.1 Input

### Endpoint

`POST /ingest`

### Request Body

| Field | Type | Description |
|------|------|-------------|
| `doc_id` | `string` | Unique document identifier |
| `source_type` | `text \| file \| url` | Source type of the document |
| `content` | `string` | Required when `source_type = text` |
| `metadata` | `object` | Optional metadata |

---

## 1.2 Main Pipeline

1. **API Layer**
   - Validate request parameters
   - Generate `trace_id`

2. **IngestService**
   - Start ingestion process
   - Record `start_time`

3. **Document Existence Check**
   - `DocRepository` checks whether `doc_id` already exists

4. **Chunking**

   `Chunker` performs text splitting:

   ```text
   content -> chunks
   ```

5. **Embedding Generation**

   `EmbeddingProvider` converts chunks into embeddings:

   ```text
   chunks -> embeddings
   ```

6. **Vector Storage**

   ```text
   VectorStore.upsert(chunks, embeddings, metadata)
   ```

7. **Graph Storage - Document Node**

   ```text
   GraphStore.upsert_document(doc_id, metadata)
   ```

8. **Graph Storage - Chunk Nodes**

   ```text
   GraphStore.upsert_chunks(doc_id, chunks)
   ```

9. **Graph Relationships**

   ```text
   GraphStore.link_doc_chunks(doc_id, chunk_ids)
   ```

10. **Optional Entity Extraction (Placeholder)**

    Reserved for future capability:

    ```text
    EntityExtractor
    ```

11. **Ingestion Logging**

    Write `IngestLog`.

    Temporary implementation may use:

    - SQLite
    - File logging

12. **Response**

    Returned fields:

    ```text
    ingest_id
    doc_id
    chunk_count
    trace_id
    timings
    ```

---

## 1.3 Idempotency and Incremental Update Strategy

### Idempotency Key

```text
doc_id
```

### Upsert Semantics

**VectorStore**

- Overwrite by `chunk_id`

**GraphStore**

- Use `MERGE` for Document and Chunk nodes

### Optional Optimization

If `content_hash` does not change:

- The ingestion pipeline may short-circuit
- The system can return immediately

This optimization can be implemented later.

---

## 1.4 Failure Handling and Retry

### External Dependency Failure

Examples:

- Milvus
- Neo4j

Handling strategy:

```text
HTTP 503
error_code = DEPENDENCY_UNAVAILABLE
```

Log fields:

```text
trace_id
dependency_name
exception_stack
```

### Invalid Input

```text
HTTP 400
error_code = INVALID_ARGUMENT
```

### Idempotency Conflict

If optimistic locking is used:

```text
HTTP 409
error_code = CONFLICT
```

---

# 2. Query Flow

## 2.1 Input

### Endpoint

`POST /query`

### Request Body

| Field | Type | Description |
|------|------|-------------|
| `query` | `string` | User query |
| `mode` | `vector_only \| graph_only \| hybrid` | Retrieval mode |
| `top_k` | `int` | Number of retrieved chunks (default = 8) |
| `filters` | `object` | Optional filtering conditions |

---

## 2.2 Main Pipeline

1. **API Layer**
   - Validate request parameters
   - Generate `trace_id`

2. **QueryService**
   - Start query execution
   - Record timing metrics

3. **Retrieval Stage**

   Depending on `mode`:

   **Vector Retrieval**

   ```text
   VectorRetriever.search(query) -> chunks
   ```

   **Graph Retrieval**

   ```text
   GraphRetriever.search(query) -> chunks
   ```

   **Hybrid Retrieval**

   - Run vector retrieval and graph retrieval in parallel
   - Merge results
   - Deduplicate
   - Truncate to `top_k`

4. **RAG Kernel**

   Implemented via a LlamaIndex `QueryEngine` wrapper.

   Input:

   ```text
   query + retrieved chunks
   ```

   Output:

   ```text
   answer
   citations (referenced chunk_ids)
   ```

5. **Response Assembly**

   Response includes:

   ```text
   trace_id
   timings
   retrieval_debug
   ```

6. **Return**

   ```text
   HTTP 200
   ```

---

## 2.3 Failure Handling

### LLM Unavailable

```text
HTTP 503
error_code = LLM_UNAVAILABLE
```

`retrieval_debug` should still be returned for troubleshooting.

### No Retrieval Results

Response answer:

```text
No relevant content was retrieved.
```

`citations` will be empty.

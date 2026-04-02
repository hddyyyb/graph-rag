# QueryService

## 1. Purpose

`QueryService` is the application-layer orchestrator for the full query pipeline.

It is the central workflow controller of the GraphRAG system.

Its job is to coordinate:

- query validation
- embedding generation
- vector retrieval
- graph retrieval
- hybrid fusion
- post-processing
- answer generation
- retrieval observability

---

## 2. High-Level Query Flow

```text
Query
→ Normalize options
→ Validate query
→ Embed query
→ Vector retrieval
→ Graph retrieval
→ Fusion
→ Postprocess
→ Answer generation
→ Build retrieval_debug
```

## 3. Constructor Dependencies

`QueryService` depends only on Ports and domain-layer objects.

```vector_store: VectorStorePort```
Used for embedding-based vector retrieval.

```graph_store: GraphStorePort```
Used for graph-based retrieval.

```embedder: EmbeddingProviderPort```
Used to generate query embeddings.

```kernel: RAGKernelPort```
Used to generate final answer text from retrieved contexts.

```trace: TracePort```
Used for tracing, events, timing metrics, and failure visibility.

```post_processor: RetrievalPostProcessorPort```
Used to sort, filter, deduplicate, and finalize candidate chunks.

### Config Fields

- `vector_top_k: int = 5`
- `graph_top_k: int = 5`
- `fusion_alpha: float = 1.0`
- `fusion_beta: float = 1.0`

These fields define default retrieval and fusion behavior.

---

## 4. Stored Fields

The class stores:

- vector store dependency
- graph store dependency
- embedder dependency
- kernel dependency
- trace dependency
- post-processor dependency
- vector retrieval default top_k
- graph retrieval default top_k
- fusion alpha
- fusion beta

---

## 5. Helper Methods

### ```5.1 _make_chunk_key(chunk)```

#### Purpose:
Build a stable merge key for retrieval fusion.

#### Output:
A tuple:
```python
(doc_id, chunk_id)
```

This key is used to deduplicate vector hits and graph hits referring to the same chunk.

---

### 5.2 ```_safe_score(chunk)```

#### Purpose:
Safely convert chunk score into float.

#### Behavior:

- returns `0.0` if `chunk.score is None`
- otherwise returns `float(chunk.score)`

Used to make fusion math safe and deterministic.

---

## 6. Fusion Logic

### ```6.1 _fuse_chunks(vector_chunks, graph_chunks)```

#### Purpose:
Merge vector retrieval results and graph retrieval results into a unified candidate set.

#### Input:

- ```vector_chunks: list[RetrievedChunk]```
- ```graph_chunks: list[RetrievedChunk]```

#### Output:

- ```fused_chunks: list[RetrievedChunk]```
- ```fusion_debug: dict```

---

### 6.2 Fusion Rules

For each chunk identity `(doc_id, chunk_id)`:

- preserve hit source information
- track whether it was retrieved by vector
- track whether it was retrieved by graph

Final score:

```final_score = alpha * vector_score + beta * graph_score```

Source labels:

- ```vector```
- ```graph```
- ```hybrid```

---

### 6.3 Fusion Debug Structure

Fusion debug includes:

- alpha
- beta
- input counts
- output count
- per-chunk source/hit/score details

---

## 7. Validation and Failure Handling

### ```7.1 _validate_query(query)```

#### Purpose:
Reject empty query input.

#### Rule:
Trim the query string and raise `ValidationError` if empty.

---

### 7.2 _handle_query_failure(stage, error)

#### Purpose:
Convert internal failures into a structured application-level query exception.

#### Behavior:

- records trace event "query_failed"
- includes:
  - trace_id
  - stage
  - error_type
  - error_message
- raises QueryExecutionError

#### Stages:

- embedding
- retrieval
- postprocess
- generation

---

## 8. Top-K Resolution

### 8.1 _resolve_top_k_values(opts)

Purpose:
Resolve actual retrieval and output top_k values.

Output:

```python
(vector_k, graph_k, final_top_k)
```

Rule:

- if opts.top_k is set → use it everywhere
- otherwise:
  - vector uses self.vector_top_k
  - graph uses self.graph_top_k
  - final uses self.vector_top_k

---

## 9. Retrieval Stage

### 9.1 _retrieve_chunks(...)

Purpose:
Run vector retrieval and graph retrieval, and collect timings.

Output:

- vector_chunks
- graph_chunks
- graph_debug
- timings

---

### 9.2 Vector Retrieval

If enable_vector is True:

- call `vector_store.search(query_embedding=qemb, top_k=vector_k)`
- record timing
- emit `vector_retrieved`

---

### 9.3 Graph Retrieval

If enable_graph is True:

- call `graph_store.search(query=q, top_k=graph_k)`
- optionally call `graph_store.get_last_debug()`
- record timing
- emit `graph_retrieved`

---

## 10. Retrieval Debug

### 10.1 ```_build_retrieval_debug(...)```

#### Purpose:
Construct final `retrieval_debug` payload.

#### Top-Level Structure:
```json
{
  "vector": { "...": "..." },
  "graph": { "...": "..." },
  "fusion": { "...": "..." },
  "merged": { "...": "..." },
  "timings": { "...": "..." },
  "stats": { "...": "..." }
}
```

#### Sections
```vector```

Contains vector retrieval hit summary.

```graph```

Contains graph retrieval hit summary and, if available, graph-specific debug payload.

```fusion```

Contains hybrid merge details.

```merged```

Contains final merged chunk preview.

```timings```

Contains per-stage elapsed time.

```stats```

Contains counts such as:

- `vector_count`
- `graph_count`
- `fusion_count`
- `citation_count`

---

## 11. Postprocess Stage

### 11.1 ```_postprocess_chunks(...)```

#### Purpose:
Apply final filtering and ranking.

#### Behavior:
Delegates to:

```python
self.post_processor.process(...)
```

Expected post-processing responsibilities include:

- sorting
- min_score filtering
- deduplication
- `top_k` trimming
- citation extraction

#### Output

Returns processed result object.

Expected semantic fields include:

- `chunks`
- `citations`

Also updates:

- `postprocess_time`
- `stats["citation_count"]`

---

## 12. Generation Stage

### 12.1 _generate_answer_text(...)

#### Purpose:
Generate final answer text.

#### Behavior:
Call:
```python
self.kernel.generate_answer(query, contexts)
```

#### Output

Returns the final answer text string.

Also updates:

- `llm_generation_time`
---

## 13. Final Answer Assembly

### 13.1 ```_build_answer(...)```

#### Purpose:
Construct final `Answer` object.

Includes:

- answer
- trace_id
- retrieval_debug
- citations

---

## 14. Public Entry Point

### 14.1 query(...)

```python
query(
    *,
    query: str,
    options: Optional[QueryOptions] = None,
    top_k: Optional[int] = None,
    min_score: Optional[float] = None,
    enable_graph: Optional[bool] = None,
    enable_vector: Optional[bool] = None,
) -> Answer
```

#### Purpose:
Execute full query pipeline.

#### Input:

- query
- QueryOptions or overrides

#### Output:

Returns `Answer`.

Expected semantic content includes:

- `answer`
- `trace_id`
- `retrieval_debug`
- `citations`

---

## 15. Execution Sequence

1. normalize options   
    Call `normalize_query_options(...)`.
2. validate query  
    Reject empty query.
3. resolve top_k  
    Compute retrieval and final output `top_k`.
4. init timings/stats  
    Prepare observability state.
5. trace start  
    Trace contains query context and effective retrieval settings.
6. embed query  
    Call `embedder.embed_query(...)`.
7. retrieve vector and graph chunks  
    Call `_retrieve_chunks(...)`.
8. Update retrieval counts  
    Populate vector and graph counts.
9. fuse  
    Call `_fuse_chunks(...)`.
10. postprocess  
    Call `_postprocess_chunks(...)`.
11. generate  
    Call `_generate_answer_text(...)`.
12. build answer  
    Call `_build_answer(...)`.

---

## 16. Observability

Events:

- query_start
- vector_retrieved
- graph_retrieved
- retrieval_timing
- query_failed
- query_done

retrieval_debug explains:

- vector hits
- graph hits
- fusion behavior
- timings
- counts

---

## 17. Design Strengths

#### Backend-agnostic orchestration

The service does not care whether the vector backend is in-memory or SQLite, or whether the graph backend is in-memory or Neo4j.

#### Explainable hybrid retrieval

Fusion is not a hidden merge step.
Its hit sources and scores are visible.

#### Structured failure handling

Embedding, retrieval, postprocess, and generation failures are mapped to explicit stages.

#### Good testability

Most methods are deterministic and Port-based, which makes service-level tests easy to write.

---

## 18. Scope Boundary

Not included:

- reranker
- multi-hop graph reasoning
- learned fusion
- evaluation benchmark

Focus: system engineering quality
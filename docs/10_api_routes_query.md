# routes/query.py

This file defines the `/query` endpoint of the GraphRAG system.

It is responsible for receiving user queries and delegating the retrieval and answer generation workflow to `QueryService`.

---

## 1. Purpose

The `/query` route is the HTTP entry point for query execution.

Its responsibilities are:

- validate query request payloads
- resolve required runtime dependencies
- call `QueryService`
- convert the service result into a response schema

The route itself does not implement retrieval, fusion, ranking, or answer generation.

---

## 2. Router Definition

```python
router = APIRouter()
```

Creates a FastAPI router instance for this module.

---

## 3. Dependency Providers

### Get query service

```python
def get_query_service(request: Request) -> QueryService:
    return request.app.state.container["query_service"]
```

Returns the shared `QueryService` instance from the application container.

### Get trace

```python
def get_trace(request: Request) -> TracePort:
    return request.app.state.container["trace"]
```

Returns the shared tracing object.

---

## 4. Endpoint Definition

```python
@router.post("/query", response_model=QueryResponse)
def query(
    payload: QueryRequest,
    svc: QueryService = Depends(get_query_service),
    trace: TracePort = Depends(get_trace),
) -> QueryResponse:
    ans = svc.query(
        query=payload.query,
        top_k=payload.top_k,
        enable_graph=payload.enable_graph,
        enable_vector=payload.enable_vector,
    )
    return QueryResponse(
        answer=ans.answer,
        trace_id=ans.trace_id,
        retrieval_debug=ans.retrieval_debug,
        citations=ans.citations,
    )
```

This defines the HTTP POST endpoint for querying the GraphRAG system.

---

## 5. Request Schema

The request body is validated using:

```python
payload: QueryRequest
```

This ensures the request satisfies the API contract before the service is called.

---

## 6. Response Schema

The route declares:

```python
response_model=QueryResponse
```

This ensures the returned response follows the expected output structure.

---

## 7. Dependency Injection

The route uses FastAPI dependency injection:

```python
svc: QueryService = Depends(get_query_service)
trace: TracePort = Depends(get_trace)
```

This keeps the route decoupled from concrete object construction.

---

## 8. Request Handling Flow

The runtime flow is:

1. FastAPI receives the request
2. request body is validated as `QueryRequest`
3. `QueryService` is resolved from the container
4. `TracePort` is resolved from the container
5. route calls `svc.query(...)`
6. service performs retrieval and answer generation
7. route converts the result into `QueryResponse`
8. response is returned to the client

---

## 9. Service Call

The core logic is:

```python
ans = svc.query(
    query=payload.query,
    top_k=payload.top_k,
    enable_graph=payload.enable_graph,
    enable_vector=payload.enable_vector,
)
```

This delegates all query-related business logic to the Application layer.

The service may perform:

- query validation
- query embedding
- vector retrieval
- graph retrieval
- fusion of candidates
- post-processing
- LLM-based answer generation

---

## 10. Response Construction

The route returns:

```python
QueryResponse(
    answer=ans.answer,
    trace_id=ans.trace_id,
    retrieval_debug=ans.retrieval_debug,
    citations=ans.citations,
)
```

### Returned fields

- `answer`: final generated answer
- `trace_id`: request-level trace identifier
- `retrieval_debug`: debug and observability details for retrieval
- `citations`: supporting retrieved chunks or metadata

---

## 11. Example Request

```json
{
  "query": "What is GraphRAG?",
  "top_k": 5,
  "enable_graph": true,
  "enable_vector": true
}
```

---

## 12. Example Response

```json
{
  "answer": "GraphRAG is a retrieval-augmented generation system that combines vector and graph retrieval.",
  "trace_id": "abc123xyz",
  "retrieval_debug": {
    "vector": {},
    "graph": {},
    "fusion": {}
  },
  "citations": [
    {
      "doc_id": "doc-001",
      "chunk_id": "chunk-0"
    }
  ]
}
```

---

## 13. Observability

This endpoint exposes observability signals through:

- `trace_id`
- `retrieval_debug`

This is important for:

- debugging retrieval behavior
- inspecting graph/vector contribution
- validating system behavior during testing

---

## 14. Design Notes

This route demonstrates the same thin-route design as the ingest endpoint:

- validate input through schema models
- resolve dependencies through the container
- call application service
- format output with a response model

This pattern keeps the API layer stable and maintainable.

---

## 15. Summary

`routes/query.py` is the HTTP adapter for the query use case.

It accepts query input, delegates execution to `QueryService`, and returns the generated answer together with tracing and retrieval debug information.
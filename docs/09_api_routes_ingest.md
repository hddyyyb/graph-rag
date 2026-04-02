# routes/ingest.py

This file defines the `/ingest` endpoint of the GraphRAG system.

It is responsible for receiving ingestion requests from clients and delegating the actual ingestion pipeline to `IngestService`.

---

## 1. Purpose

The `/ingest` route is the HTTP entry point for document ingestion.

Its responsibilities are:

- validate request payloads
- resolve runtime dependencies
- call the application service
- convert service output into an API response model

It does not implement chunking, embedding, vector writing, or graph writing itself.

---

## 2. Router Definition

```python
router = APIRouter()
```

This creates a FastAPI router that can later be registered in `api/main.py`.

---

## 3. Dependency Providers

The file defines several helper functions for retrieving shared runtime objects from the application container.

### Get container

```python
def get_container(request: Request):
    return request.app.state.container
```

Returns the container dictionary attached to the FastAPI app.

### Get ingest service

```python
def get_ingest_service(request: Request) -> IngestService:
    return request.app.state.container["ingest_service"]
```

Returns the shared `IngestService` instance.

### Get trace

```python
def get_trace(request: Request) -> TracePort:
    return request.app.state.container["trace"]
```

Returns the shared tracing object.

### Get settings

```python
def get_settings(request: Request) -> Settings:
    return request.app.state.container["settings"]
```

Returns the runtime settings object.

---

## 4. Endpoint Definition

```python
@router.post("/ingest", response_model=IngestResponse)
def ingest(
    payload: IngestRequest,
    svc: IngestService = Depends(get_ingest_service),
    trace: TracePort = Depends(get_trace),
) -> IngestResponse:
    res = svc.ingest(doc_id=payload.doc_id, text=payload.text, metadata=payload.metadata)
    return IngestResponse(doc_id=res.doc_id, chunks=res.chunks, trace_id=trace.get_trace_id())
```

This defines the HTTP POST endpoint for ingestion.

---

## 5. Request Schema

The request body is validated using `IngestRequest`.

```python
payload: IngestRequest
```

This means FastAPI automatically validates:

- required fields
- field types
- field constraints

---

## 6. Response Schema

The route declares:

```python
response_model=IngestResponse
```

So the response must follow the `IngestResponse` schema.

This ensures a stable output contract for clients.

---

## 7. Dependency Injection

The route uses FastAPI's dependency system:

```python
svc: IngestService = Depends(get_ingest_service)
trace: TracePort = Depends(get_trace)
```

This allows the route to remain lightweight and testable.

It does not manually instantiate any service objects.

---

## 8. Request Handling Flow

The runtime flow is:

1. FastAPI receives the request
2. request body is validated as `IngestRequest`
3. `IngestService` is resolved from the container
4. `TracePort` is resolved from the container
5. route calls `svc.ingest(...)`
6. service returns ingestion result
7. route wraps the result in `IngestResponse`
8. response is returned to the client

---

## 9. Service Call

The core line is:

```python
res = svc.ingest(
    doc_id=payload.doc_id,
    text=payload.text,
    metadata=payload.metadata,
)
```

This hands control over to the Application layer.

The service is responsible for the actual ingestion workflow, including:

- validation beyond the HTTP layer
- text chunking
- embedding generation
- vector store write
- graph store write

---

## 10. Response Construction

The route returns:

```python
IngestResponse(
    doc_id=res.doc_id,
    chunks=res.chunks,
    trace_id=trace.get_trace_id(),
)
```

### Returned fields

- `doc_id`: the ingested document identifier
- `chunks`: number of generated chunks
- `trace_id`: the current request trace id

This gives the client both the business result and the observability identifier.

---

## 11. Example Request

```json
{
  "doc_id": "doc-001",
  "text": "GraphRAG is a retrieval-augmented generation system.",
  "metadata": {
    "source": "demo"
  }
}
```

---

## 12. Example Response

```json
{
  "doc_id": "doc-001",
  "chunks": 1,
  "trace_id": "a1b2c3d4e5"
}
```

---

## 13. Design Notes

This route demonstrates a clean API-layer pattern:

- schema-based validation
- dependency injection
- service delegation
- explicit response shaping

This makes the route:

- easy to read
- easy to test
- easy to extend

---

## 14. Summary

`routes/ingest.py` is a thin HTTP adapter around the ingestion use case.

It accepts an ingestion request, forwards it to `IngestService`, and returns a structured API response with tracing information.
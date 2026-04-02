# API Layer Overview

The API layer is implemented using FastAPI and serves as the entry point of the GraphRAG system.

It is responsible for:
- HTTP request handling
- Dependency injection (via container)
- Input validation (via Pydantic schemas)
- Response formatting
- Error mapping
- Observability (trace_id propagation)

---

## Endpoints

| Method | Path     | Description          |
|--------|----------|----------------------|
| GET    | /health  | Health check         |
| POST   | /ingest  | Document ingestion   |
| POST   | /query   | Query + RAG pipeline |

---

## Architecture Role

The API layer does NOT contain business logic.

Instead, it:
- delegates work to Application Services
- enforces request/response contracts
- handles cross-cutting concerns (logging, tracing, errors)

---

## Middleware

### Trace Middleware

Each request is assigned a `trace_id`:

- extracted from header `x-trace-id`
- generated if not provided
- injected into:
  - Trace context
  - Response headers

---

## Exception Mapping

Domain exceptions are mapped to HTTP responses:

| Exception          | HTTP Status |
|--------------------|------------|
| ValidationError    | 400        |
| NotFoundError      | 404        |
| ConflictError      | 409        |
| DependencyError    | 502        |
| Exception          | 500        |

---

## Dependency Injection

All services are resolved via:

```python
request.app.state.container
```

This ensures:

- loose coupling
- testability
- backend swappability
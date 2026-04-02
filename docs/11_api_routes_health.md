# routes/health.py

This file defines the `/health` endpoint of the GraphRAG system.

It is the simplest route in the API layer and is mainly used for service availability checks.

---

## 1. Purpose

The health endpoint exists to confirm that the API process is running and able to respond to requests.

Typical use cases include:

- local development checks
- deployment smoke tests
- container liveness probes
- load balancer health checks

---

## 2. Router Definition

```python
router = APIRouter()
```

Creates a FastAPI router instance for this module.

---

## 3. Endpoint Definition

```python
@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

This defines a GET endpoint that returns a simple status payload.

---

## 4. Response Format

Example response:

```json
{
  "status": "ok"
}
```

---

## 5. Design Characteristics

This endpoint is intentionally minimal.

It does not:

- access the database
- access vector storage
- access graph storage
- call application services
- generate trace-heavy business output

Its only job is to provide a lightweight readiness signal.

---

## 6. Why It Matters

Even though the implementation is simple, this endpoint is important in production-like systems because it allows external systems to determine whether the service is alive.

Examples:

- Docker or Kubernetes health checks
- deployment verification scripts
- API gateway readiness detection

---

## 7. Summary

`routes/health.py` provides a lightweight liveness endpoint.

It returns a fixed JSON response and serves as the standard health check route of the GraphRAG API.
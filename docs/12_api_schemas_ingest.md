# schemas/ingest.py

This file defines the request and response schema models for the `/ingest` endpoint.

The models are implemented with Pydantic and are part of the HTTP contract of the API layer.

---

## 1. Purpose

These schema classes are used to:

- validate client input
- define a stable API contract
- serialize structured responses
- keep route handlers simple

---

## 2. `IngestRequest`

```python
class IngestRequest(BaseModel):
    doc_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None
```

This model defines the request body for the `/ingest` endpoint.

### Fields

#### `doc_id`

- type: `str`
- required: yes
- constraint: minimum length = 1

Represents the document identifier.

#### `text`

- type: `str`
- required: yes
- constraint: minimum length = 1

Represents the raw document text to be ingested.

#### `metadata`

- type: `Optional[Dict[str, Any]]`
- required: no
- default: `None`

Represents optional metadata associated with the document.

---

## 3. Example `IngestRequest`

```json
{
  "doc_id": "doc-001",
  "text": "This is a sample document for GraphRAG ingestion.",
  "metadata": {
    "source": "demo",
    "lang": "en"
  }
}
```

---

## 4. `IngestResponse`

```python
class IngestResponse(BaseModel):
    doc_id: str
    chunks: int
    trace_id: str
```

This model defines the response body for the `/ingest` endpoint.

### Fields

#### `doc_id`

- type: `str`

The identifier of the ingested document.

#### `chunks`

- type: `int`

The number of chunks generated during ingestion.

#### `trace_id`

- type: `str`

The request-level trace identifier for observability and debugging.

---

## 5. Example `IngestResponse`

```json
{
  "doc_id": "doc-001",
  "chunks": 4,
  "trace_id": "a1b2c3d4"
}
```

---

## 6. Validation Role

These models allow FastAPI and Pydantic to validate incoming payloads automatically.

For example:

- empty `doc_id` is rejected
- empty `text` is rejected
- invalid metadata type is rejected

This reduces manual validation code in route handlers.

---

## 7. API Design Value

Using schema models provides several benefits:

- explicit API documentation
- safer request parsing
- cleaner route functions
- easier Swagger/OpenAPI generation

---

## 8. Summary

`schemas/ingest.py` defines the HTTP data contract for document ingestion.

It contains:

- `IngestRequest` for validating client input
- `IngestResponse` for structuring server output
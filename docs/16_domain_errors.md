# Domain Errors

## Overview

This file defines the core exception hierarchy used by the domain and application layers.

The purpose of this design is to provide:

- a consistent error model
- clearer failure classification
- better error mapping in upper layers
- cleaner separation between business errors and infrastructure failures

---

## Error Hierarchy

The exception hierarchy is:

```python
DomainError
├── ValidationError
├── NotFoundError
├── ConflictError
└── DependencyError
```

---

## Base Class

### DomainError

Base class for all domain/application errors.

```python
class DomainError(Exception):
    """Base class for domain/application errors."""
```

#### Purpose

This class serves as the common parent for all controlled business-layer exceptions.

It allows the system to:

- catch domain-related failures in one place
- distinguish expected business errors from unexpected internal crashes
- map domain errors to API responses more cleanly

---

## Specific Error Types

### ValidationError

Raised when input data is invalid or violates business validation rules.

```python
class ValidationError(DomainError):
    pass
```

#### Typical Scenarios

- empty query
- invalid document payload
- illegal parameter combination
- malformed request data inside the application layer

#### Example

```python
raise ValidationError("Query must not be empty.")
```

---

### NotFoundError

Raised when a required resource cannot be found.

```python
class NotFoundError(DomainError):
    pass
```

#### Typical Scenarios

- document does not exist
- chunk does not exist
- requested object is missing in storage
- lookup by ID fails

#### Example

```python
raise NotFoundError("Document not found.")
```

---

### ConflictError

Raised when an operation conflicts with the current system state.

```python
class ConflictError(DomainError):
    pass
```

#### Typical Scenarios

- duplicate resource creation
- state transition conflict
- attempting an operation that violates uniqueness or consistency constraints

#### Example

```python
raise ConflictError("Document with the same ID already exists.")
```

---

### DependencyError

Raised when an external dependency fails.

```python
class DependencyError(DomainError):
    """External dependency failed (db, vector store, graph store, llm, etc)."""
    pass
```

#### Typical Scenarios

- database connection failure
- vector store unavailable
- graph store unavailable
- LLM backend failure
- third-party service timeout

#### Example

```python
raise DependencyError("Vector store is unavailable.")
```

---

## Why This Design Matters

A dedicated domain error hierarchy improves engineering quality in several ways:

### 1. Clear semantics

Each error type expresses a different category of failure.

### 2. Better API mapping

Upper layers can map errors to HTTP responses more precisely.

For example:

```json
{
  "error": "ValidationError",
  "message": "Query must not be empty."
}
```

Possible mappings:

- `ValidationError` → 400 Bad Request
- `NotFoundError` → 404 Not Found
- `ConflictError` → 409 Conflict
- `DependencyError` → 503 Service Unavailable

### 3. Cleaner layering

The application layer can raise meaningful domain exceptions without exposing infrastructure-specific details directly.

### 4. Easier maintenance

A centralized hierarchy makes error handling more consistent across services.

---

## Example Usage

```python
def validate_query(query: str) -> None:
    if not query.strip():
        raise ValidationError("Query must not be empty.")
```

```python
def fetch_document(doc_id: str):
    doc = repository.get(doc_id)
    if doc is None:
        raise NotFoundError(f"Document {doc_id} not found.")
    return doc
```

```python
def query_vector_store(store, embedding):
    try:
        return store.search(embedding)
    except Exception as exc:
        raise DependencyError("Vector store search failed.") from exc
```

---

## Summary

This file provides a minimal but important error system for the GraphRAG project.

It includes:

- `DomainError`: common base error
- `ValidationError`: invalid input or rule violation
- `NotFoundError`: missing resource
- `ConflictError`: state conflict
- `DependencyError`: external dependency failure

This hierarchy helps make the system more predictable, explainable, and production-friendly.
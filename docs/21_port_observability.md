# Observability Port

## Overview

This file defines the `TracePort`, which is the abstraction for trace propagation and structured event recording in the GraphRAG system.

Its purpose is to let the application layer record trace and event information without depending on any specific observability implementation.

This port supports:

- request trace ID management
- contextual field binding
- structured event logging
- retrieval of bound fields for debugging

---

## Interface

```python
from __future__ import annotations

from typing import Any, Dict, Protocol


class TracePort(Protocol):
    def get_trace_id(self) -> str:
        ...

    def set_trace_id(self, trace_id: str) -> None:
        ...

    def bind(self, **fields: Any) -> None:
        ...

    def event(self, name: str, **fields: Any) -> None:
        ...

    def get_bound_fields(self) -> Dict[str, Any]:
        ...
```

---

## Why This Port Exists

The application layer should not directly write code like this:

```python
import logging

logging.info("query started")
```

That would tightly couple business logic to a specific logging mechanism.

If the system later switches to:

- structured JSON logs
- OpenTelemetry
- Jaeger
- Datadog
- ELK
- Sentry

then application code would need to change.

With `TracePort`, the application layer only depends on an abstract interface.

---

## Methods

### `get_trace_id()`

Returns the current request trace ID.

```python
def get_trace_id(self) -> str:
    ...
```

#### Returns

- `str`: Current trace ID

#### Usage

Useful when the application wants to attach trace context to outputs such as final answers or debug payloads.

---

### `set_trace_id(trace_id)`

Sets the current request trace ID.

```python
def set_trace_id(self, trace_id: str) -> None:
    ...
```

#### Parameters

- `trace_id`: The trace identifier to store

#### Usage

Typically called in middleware at request entry.

---

### `bind(**fields)`

Binds contextual fields to the current trace scope.

```python
def bind(self, **fields: Any) -> None:
    ...
```

#### Parameters

- `**fields`: Arbitrary structured context fields

#### Usage

After binding fields such as `doc_id="doc1"`, later events can automatically include those fields.

Example:

```python
trace.bind(doc_id="doc1", operation="ingest")
```

---

### `event(name, **fields)`

Records a structured event.

```python
def event(self, name: str, **fields: Any) -> None:
    ...
```

#### Parameters

- `name`: Event name
- `**fields`: Structured event fields

#### Usage

Example:

```python
trace.event("query_start", enable_graph=True, top_k=5)
```

This is much cleaner than manually formatting log strings.

---

### `get_bound_fields()`

Returns currently bound contextual fields.

```python
def get_bound_fields(self) -> Dict[str, Any]:
    ...
```

#### Returns

- `Dict[str, Any]`: Bound context fields

#### Usage

Mostly useful for debugging or introspection.

---

## Example Usage

```python
trace.set_trace_id("trace-123")
trace.bind(doc_id="doc1", stage="query")
trace.event("query_start", enable_graph=True)
```

---

## Architectural Role

`TracePort` gives the application layer a stable way to emit observability signals.

It helps support:

- tracing
- structured logging
- debugging
- request correlation
- event-based monitoring

without introducing infrastructure dependencies into business logic.

---

## Typical Flow

```text
Middleware
  -> set_trace_id()

Application Layer
  -> bind(...)
  -> event(...)
  -> get_trace_id()

Infra Layer
  -> decides how trace/events are actually recorded
```

---

## Engineering Benefits

### 1. Decoupling

The application layer stays independent from concrete logging libraries.

### 2. Structured observability

Events can be emitted as machine-readable records instead of plain strings.

### 3. Easier backend replacement

Observability implementation can evolve without changing service code.

### 4. Better debugging

Trace IDs and bound fields make request-level debugging much easier.

---

## Summary

`TracePort` defines the observability boundary for the application layer.

It provides a clean way to handle:

- trace ID propagation
- bound context
- structured event recording
- debugging support

This is an important part of keeping the GraphRAG system production-friendly and maintainable.
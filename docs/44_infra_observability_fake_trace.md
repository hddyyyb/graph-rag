# FakeTrace

## Overview

`FakeTrace` is a lightweight test implementation of `TracePort`.

It is designed for unit tests, service tests, and lightweight local runs where you want deterministic trace behavior without depending on the real logging or runtime tracing system. It stores a fixed trace ID by default and keeps bound fields in memory. :contentReference[oaicite:2]{index=2}

## Purpose

This class exists to make observability-related behavior testable without introducing side effects such as:

- writing logs
- generating random trace IDs
- depending on async runtime context
- coupling tests to the real logging setup

Because it implements the same `TracePort` contract as the production trace implementation, it can be injected into application services in exactly the same way. :contentReference[oaicite:3]{index=3}

## Behavior

### Default trace ID

When initialized, `FakeTrace` starts with a deterministic default trace ID:

'''python
trace_test_999
'''

This makes assertions in tests straightforward and stable. :contentReference[oaicite:4]{index=4}

### Bound fields

The instance stores bound fields in an internal dictionary. Calling `bind(**fields)` updates that dictionary in place, allowing tests to inspect which contextual fields were attached during execution. :contentReference[oaicite:5]{index=5}

### Event handling

`event(name, **fields)` is intentionally implemented as a no-op. This means tests can execute instrumentation code without requiring actual log output or event transport. :contentReference[oaicite:6]{index=6}

## Public API

### `get_trace_id() -> str`

Returns the current trace ID. :contentReference[oaicite:7]{index=7}

### `set_trace_id(trace_id: str) -> None`

Overrides the stored trace ID. This is useful when a test needs to simulate a specific request or correlation ID. :contentReference[oaicite:8]{index=8}

### `bind(**fields: Any) -> None`

Adds or updates contextual fields associated with the current trace. Later calls overwrite keys with the same name. :contentReference[oaicite:9]{index=9}

### `event(name: str, **fields: Any) -> None`

Accepts an event name and optional event fields, but does nothing. This preserves interface compatibility while keeping the fake implementation side-effect free. :contentReference[oaicite:10]{index=10}

### `get_bound_fields() -> Dict[str, Any]`

Returns a shallow copy of the currently bound fields. Returning a copy prevents external callers from mutating internal state directly. :contentReference[oaicite:11]{index=11}

## Example

'''python
from graph_rag.infra.observability.fake_trace import FakeTrace

trace = FakeTrace()

assert trace.get_trace_id() == "trace_test_999"

trace.bind(user_id="u1", doc_id="doc_123")
assert trace.get_bound_fields() == {
    "user_id": "u1",
    "doc_id": "doc_123",
}

trace.set_trace_id("trace_case_001")
assert trace.get_trace_id() == "trace_case_001"

trace.event("query_started", query="What is GraphRAG?")
'''

## When to use

Use `FakeTrace` when:

- writing unit tests for application services
- validating that trace fields are bound correctly
- testing code paths that expect a `TracePort`
- avoiding dependency on the real logging system

## When not to use

Do not use `FakeTrace` in production-style runtime wiring when you need:

- per-request trace isolation
- generated trace IDs
- event log emission
- integration with the configured logger

## Design notes

`FakeTrace` follows the same port-driven architecture as the rest of the project. The application layer depends only on `TracePort`, not on a concrete implementation. This allows the system to swap between fake and real observability implementations without changing service logic. That aligns with the project’s Clean Architecture approach and explicit port design. :contentReference[oaicite:12]{index=12}
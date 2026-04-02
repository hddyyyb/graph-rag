# Clock Port

## Overview

This file defines the `ClockPort`, which is the abstraction for time access in the GraphRAG system.

Instead of calling system time APIs directly inside business logic, the application layer can depend on this interface.

This helps keep time-related behavior:

- testable
- deterministic
- decoupled from environment details

---

## Interface

```python
from typing import Protocol

class ClockPort(Protocol):
    def now_iso(self) -> str:
        ...
```

---

## Method

### `now_iso()`

Returns the current time as an ISO-formatted string.

```python
def now_iso(self) -> str:
    ...
```

#### Returns

- `str`: Current timestamp in ISO string format

---

## Why This Port Exists

Directly calling system time inside application logic can make testing harder.

For example, code like this is inconvenient to test:

```python
from datetime import datetime

timestamp = datetime.utcnow().isoformat()
```

By using `ClockPort`, the application layer does not care how time is produced.

A concrete implementation may return:

- real current time
- fixed time in tests
- mocked time in controlled scenarios

---

## Example Usage

```python
timestamp = clock.now_iso()
```

This can then be used for:

- response metadata
- event timestamps
- debug payloads
- audit fields

---

## Design Benefits

### 1. Testability

Tests can inject a fake clock with deterministic output.

### 2. Decoupling

Business logic does not depend on concrete datetime APIs.

### 3. Consistency

Time formatting can be standardized in one place.

---

## Typical Role in the System

A clock port is especially useful when generating structured output fields such as:

- timestamps in answer payloads
- event logs
- debug metadata

---

## Summary

`ClockPort` defines a minimal but useful abstraction for time access.

It allows the GraphRAG system to handle time in a cleaner and more testable way.
# `infra.adapters.clock`

## Overview

This module provides concrete clock adapters for the `ClockPort`-style time access pattern.

It includes:
- `SystemClock`: returns the current real time
- `FixedClock`: returns a fixed predefined timestamp string

These adapters are useful for production code and tests respectively.

## Classes

## `SystemClock`

### Purpose

`SystemClock` is the runtime clock implementation. It returns the current time in ISO 8601 format using the `Asia/Shanghai` timezone.

### Methods

#### `now_iso() -> str`

Returns the current time as an ISO-formatted string.

### Behavior

```python
clock = SystemClock()
timestamp = clock.now_iso()
```

Possible output:

```json
"2026-04-02T13:45:12.123456+08:00"
```

### Notes

- Uses `datetime.now(ZoneInfo("Asia/Shanghai"))`
- Returns a string rather than a `datetime` object
- Suitable for logging, tracing, and API metadata

---

## `FixedClock`

### Purpose

`FixedClock` is a deterministic clock for tests.

Instead of reading the current system time, it always returns the same preconfigured string.

### Constructor

#### `__init__(txt)`

**Parameters**
- `txt`: the timestamp string to return later

### Methods

#### `now_iso() -> str`

Returns the fixed string that was passed into the constructor.

### Example

```python
clock = FixedClock("2026-04-02T10:00:00+08:00")
assert clock.now_iso() == "2026-04-02T10:00:00+08:00"
```

## Use Cases

### Production
Use `SystemClock` when the application should use real wall-clock time.

### Testing
Use `FixedClock` when reproducibility is required.

## Design Notes

- Very small adapter module by design
- Keeps time access injectable
- Avoids hard-coding `datetime.now()` throughout the codebase
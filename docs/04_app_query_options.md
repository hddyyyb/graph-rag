# QueryOptions and Query Parameter Normalization

## 1. Purpose

`query_option.py` defines the query-time configuration model used by `QueryService`.

It solves two problems:

1. represent query retrieval options in a structured way
2. normalize mixed input sources into a single `QueryOptions` object

---

## 2. Class: `QueryOptions`

```python
@dataclass(frozen=True)
class QueryOptions:
    top_k: Optional[int] = None
    min_score: Optional[float] = None
    enable_vector: bool = True
    enable_graph: bool = True
```
# Role

```QueryOptions``` is an immutable configuration object for one query execution.

# Fields
```top_k: Optional[int]```
Controls the candidate count used during retrieval and final post-processing.

```min_score: Optional[float]```
Optional score threshold used in post-processing.

```enable_vector: bool = True```
Whether vector retrieval is enabled.

```enable_graph: bool = True```
Whether graph retrieval is enabled.

---

# 3. Why ```frozen=True```

The dataclass is immutable.

Benefits:
- avoids accidental mutation during query flow
- makes options easier to reason about
- supports explicit override behavior

---

# 4. Boolean Semantics

```enable_vector``` and ```enable_graph``` are NOT tri-state flags.

They mean:

- ```True``` → enable that retrieval path
- ```False``` → disable that retrieval path

They do NOT mean:

- ```None``` → use default

This keeps retrieval behavior explicit.

---

# 5. ```normalize_query_options(...)```
```python
normalize_query_options(
    options: Optional[QueryOptions] = None,
    top_k: Optional[int] = None,
    min_score: Optional[float] = None,
    enable_graph: Optional[bool] = None,
    enable_vector: Optional[bool] = None,
) -> QueryOptions
```
## Purpose

Merge:

- an optional base ```QueryOptions```
- plus optional per-call override parameters

into one final ```QueryOptions``` object.

---

# 6. Normalization Rule

Normalization logic is:

- if a function argument is explicitly provided, use it
- otherwise fall back to the corresponding field from ```options```
- if ```options``` is not provided, use the default ```QueryOptions()```

In short:
```explicit override > options object > dataclass default```

---

# 7. Example
## Base options only
```python
opts = QueryOptions(top_k=5, enable_graph=False)
normalize_query_options(options=opts)
```
Result:
```python
QueryOptions(top_k=5, min_score=None, enable_vector=True, enable_graph=False)
```
## Override one field
```python
opts = QueryOptions(top_k=5, enable_graph=False)
normalize_query_options(options=opts, enable_graph=True)
```
Result:
```python
QueryOptions(top_k=5, min_score=None, enable_vector=True, enable_graph=True)
```
# 8. Why This Matters

This utility gives ```QueryService``` a simple and stable input contract.

Callers may choose either:

- object-style configuration
- per-call named overrides
- or a mix of both

The service still receives one normalized structure.

This reduces branching and keeps query orchestration clean.
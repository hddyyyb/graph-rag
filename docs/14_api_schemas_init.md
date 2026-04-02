# schemas/__init__.py

This file is the central export entry of the `schemas` package.

It re-exports commonly used schema models so that other modules can import them more conveniently.

---

## 1. Source Code

```python
from .ingest import IngestRequest, IngestResponse
from .query import QueryRequest, QueryResponse

__all__ = ["IngestRequest", "IngestResponse", "QueryRequest", "QueryResponse"]
```

---

## 2. Purpose

Without this file, importing schema models would require direct submodule paths such as:

```python
from graph_rag.api.schemas.ingest import IngestRequest
from graph_rag.api.schemas.query import QueryRequest
```

With this package-level export file, imports can be simplified to:

```python
from graph_rag.api.schemas import IngestRequest, QueryRequest
```

This improves readability and makes the import surface cleaner.

---

## 3. Exported Models

The file currently exposes four schema classes:

- `IngestRequest`
- `IngestResponse`
- `QueryRequest`
- `QueryResponse`

---

## 4. Role of `__all__`

The `__all__` list explicitly defines the public API of the `schemas` package.

```python
__all__ = ["IngestRequest", "IngestResponse", "QueryRequest", "QueryResponse"]
```

This helps make package exports more intentional and easier to understand.

---

## 5. Design Benefit

A package-level export file provides:

- shorter import paths
- cleaner module boundaries
- more maintainable public API organization

This is a small but useful engineering detail in larger projects.

---

## 6. Summary

`schemas/__init__.py` is the package export file for API schemas.

It re-exports request and response models for easier import and clearer package structure.
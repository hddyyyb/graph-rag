# Postprocess Models

## Overview

This file defines the result model returned by retrieval post-processing.

It introduces a lightweight immutable container that bundles:

- processed chunk results
- extracted citation data

This model is used as the output contract of the retrieval post-processing stage.

---

## Class

### ProcessedResults

Represents the final output of retrieval post-processing.

```python
from dataclasses import dataclass
from typing import List, Dict, Any

from graph_rag.domain.models import RetrievedChunk


@dataclass(frozen=True)
class ProcessedResults:
    chunks: List[RetrievedChunk]
    citations: List[Dict[str, Any]]
```

---

## Fields

### `chunks`

The final list of processed retrieval chunks.

Type:

```python
List[RetrievedChunk]
```

These are typically the chunks that remain after steps such as:

- sorting
- filtering
- deduplication
- top-k truncation

---

### `citations`

The citation metadata derived from the processed chunk list.

Type:

```python
List[Dict[str, Any]]
```

The exact structure of each citation dictionary depends on the implementation, but it usually contains identifying information such as:

- document ID
- chunk ID
- source
- text snippet or related metadata

---

## Why This Model Exists

The post-processing stage returns more than just chunks.

It often also produces citation information for downstream use in:

- answer rendering
- API responses
- debugging
- grounding inspection

Returning both outputs as a structured object is cleaner than returning a tuple or raw dictionary.

---

## Example

```python
results = ProcessedResults(
    chunks=[
        RetrievedChunk(
            doc_id="doc1",
            chunk_id="c1",
            text="GraphRAG combines vector and graph retrieval.",
            score=0.95,
            source="hybrid",
        )
    ],
    citations=[
        {
            "doc_id": "doc1",
            "chunk_id": "c1",
            "source": "hybrid",
        }
    ],
)
```

---

## Architectural Role

This model belongs to the post-processing boundary.

It is typically produced by a `RetrievalPostProcessorPort` implementation and then consumed by higher-level services such as `QueryService`.

---

## Summary

`ProcessedResults` is a simple immutable container for retrieval post-processing output.

It keeps the post-processing stage explicit and structured by bundling:

- final chunks
- citation metadata
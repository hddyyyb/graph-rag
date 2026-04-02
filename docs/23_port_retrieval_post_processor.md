# Retrieval Post Processor Port

## Overview

This file defines the `RetrievalPostProcessorPort`, which is the abstraction for retrieval result post-processing in the GraphRAG system.

It represents the stage that takes raw retrieved chunks and transforms them into final retrieval outputs suitable for answer generation and API return.

Typical responsibilities of a post-processor include:

- sorting
- score filtering
- deduplication
- top-k truncation
- citation extraction

---

## Interface

```python
from __future__ import annotations

from typing import Protocol, List, Optional

from graph_rag.domain.models import RetrievedChunk
from graph_rag.ports.postprocess_models import ProcessedResults


class RetrievalPostProcessorPort(Protocol):
    def process(self, chunks: List[RetrievedChunk], top_k: int, min_score: Optional[float] = None) -> ProcessedResults:
        ...
```

---

## Method

### `process(chunks, top_k, min_score=None)`

Processes raw retrieval results into final structured output.

```python
def process(
    self,
    chunks: List[RetrievedChunk],
    top_k: int,
    min_score: Optional[float] = None
) -> ProcessedResults:
    ...
```

#### Parameters

- `chunks`: Raw retrieved chunk list
- `top_k`: Maximum number of chunks to keep
- `min_score`: Optional minimum score threshold

#### Returns

- `ProcessedResults`: Final processed chunks and citations

---

## Input and Output

The intended contract is:

### Input

- raw retrieval results
- top-k constraint
- optional score threshold

### Output

- processed result chunks
- citations

---

## Why This Port Exists

Raw retrieval output is usually not ready for direct use.

Multiple retrieval backends may produce:

- duplicate chunks
- noisy low-score items
- unsorted results
- inconsistent source mixtures

The post-processing stage centralizes cleanup and normalization.

This is important because it keeps retrieval orchestration and result cleanup separate.

---

## Typical Responsibilities

Although the interface itself does not enforce a specific algorithm, a concrete implementation commonly performs:

### 1. Sorting

Sort chunks by score in descending order.

### 2. Filtering

Remove chunks below `min_score`.

### 3. Deduplication

Merge or remove duplicate chunk entries.

### 4. Top-k limiting

Keep only the top `k` results.

### 5. Citation generation

Build citation metadata from final chunks.

---

## Example Usage

```python
processed = post_processor.process(
    chunks=retrieved_chunks,
    top_k=5,
    min_score=0.3,
)

final_chunks = processed.chunks
citations = processed.citations
```

---

## Architectural Position

```text
Vector / Graph Retrieval
  -> raw RetrievedChunk list
  -> RetrievalPostProcessorPort.process(...)
  -> ProcessedResults
  -> answer generation / API response
```

---

## Design Benefits

### Separation of concerns

Retrieval backends focus on finding candidates.  
The post-processor focuses on cleaning and structuring them.

### Reusability

The same post-processing logic can be reused for:

- vector-only retrieval
- graph-only retrieval
- hybrid retrieval

### Testability

Sorting, filtering, deduplication, and citation generation can be tested independently.

---

## Summary

`RetrievalPostProcessorPort` defines the post-processing boundary for retrieval results.

It standardizes how raw retrieval candidates become:

- final chunk outputs
- citation metadata

This helps keep the GraphRAG pipeline modular and maintainable.
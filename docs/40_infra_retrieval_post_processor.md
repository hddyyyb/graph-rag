# `infra.adapters.retrieval_post_processor`

## Overview

This module provides `DefaultRetrievalPostProcessor`, the default implementation of `RetrievalPostProcessorPort`.

It transforms raw retrieval results into final ranked results and lightweight citation metadata.

## Processing Pipeline

The processor performs the following steps:

1. sort by score descending
2. optionally filter by `min_score`
3. deduplicate
4. trim to `top_k`
5. build citations

## Class

## `DefaultRetrievalPostProcessor`

### Purpose

This adapter standardizes the final result selection stage after vector retrieval, graph retrieval, or hybrid fusion.

It separates low-level retrieval from final ranking cleanup.

## Methods

### `process(chunks: List[RetrievedChunk], top_k: int, min_score: Optional[float] = None) -> ProcessedResults`

Processes the raw chunk list and returns a `ProcessedResults` object.

## Inputs

- `chunks`: raw retrieved chunk list
- `top_k`: maximum number of results to keep
- `min_score`: optional score threshold

## Output

Returns `ProcessedResults` with:
- `chunks`: final selected `RetrievedChunk` list
- `citations`: citation metadata list

## Deduplication Rule

The processor deduplicates by:

```python
(doc_id, chunk_id, source)
```

This means the same chunk from the same source will appear only once in the final output.

## Citation Structure

Each citation is a dictionary like:

```json
{
  "doc_id": "doc1",
  "chunk_id": "c3",
  "source": "graph",
  "score": 0.83
}
```

## Example

```python
processor = DefaultRetrievalPostProcessor()

processed = processor.process(
    chunks=retrieved_chunks,
    top_k=5,
    min_score=0.2,
)
```

## Why This Module Matters

This module keeps retrieval post-processing:
- consistent
- testable
- reusable
- independent from specific store implementations

## Limitations

- sorting uses score only
- no source-aware reranking
- no reciprocal rank fusion or advanced calibration
- no citation formatting beyond flat metadata
# `infra.adapters.fake_embedding_v2`

## Overview

This module provides `FakeEmbeddingV2`, an extremely simple fake embedding generator.

It returns fixed-value vectors and is mainly useful for smoke tests or very early integration checks.

## Class

## `FakeEmbeddingV2`

### Purpose

`FakeEmbeddingV2` produces deterministic embeddings where:
- every vector has the same length
- most values are `1`
- the first value is always `999`

This makes outputs easy to recognize during debugging.

## Constructor

### `__init__(dim=32)`

**Parameters**
- `dim`: vector dimension

**Instance Attributes**
- `dim`: embedding dimension

## Methods

### `embed_texts(texts: List[str]) -> List[List[float]]`

Generates one fake embedding per input text.

**Input**
- `texts`: list of strings

**Output**
- list of vectors

### `embed_query(query: str) -> List[float]`

Generates one fake embedding for a query.

**Input**
- `query`: query text

**Output**
- one vector

### `_emb_one(text: str) -> List[float]`

Internal helper that builds a single vector.

Behavior:
- creates a list of length `dim`
- fills it with `1`
- sets the first element to `999`

## Example Output

For `dim=4`, the output is:

```json
[999, 1, 1, 1]
```

## Example

```python
embedder = FakeEmbeddingV2(dim=4)

doc_vectors = embedder.embed_texts(["a", "b"])
query_vector = embedder.embed_query("hello")
```

## Notes

- The output does not depend on the text content.
- This is intentionally unrealistic.
- It is useful only for adapter wiring tests or trivial behavior checks.

## Limitations

- no semantic meaning
- no input sensitivity
- poor fit for retrieval ranking validation

## Best Use Cases

- verifying that embedding calls are wired correctly
- testing store write/read flow
- avoiding external dependencies in fast tests
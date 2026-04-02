# `infra.adapters.sentence_transformer_embedding`

## Overview

This module provides `SentenceTransformerEmbeddingProvider`, a real embedding backend built on `sentence-transformers`.

It implements `EmbeddingProviderPort` and is the semantic embedding adapter for the system.

## Class

## `SentenceTransformerEmbeddingProvider`

### Purpose

This adapter turns text into semantic vector embeddings using a local or downloaded SentenceTransformer model.

It is appropriate for:
- real retrieval
- local embedding generation
- experiments with normalized or raw embeddings

## Constructor

```python
SentenceTransformerEmbeddingProvider(
    model_name_or_path: str = r"E:/Reasarch/hf_models/all-MiniLM-L6-v2",
    normalize_embeddings: bool = False,
) -> None
```

### Parameters

- `model_name_or_path`: model path or model name
- `normalize_embeddings`: whether embeddings should be normalized during encoding

### Instance Attributes

- `model`: loaded `SentenceTransformer`
- `normalize_embeddings`: normalization flag

## Methods

### `embed_texts(texts: List[str]) -> List[List[float]]`

Encodes a list of texts.

### Behavior
- returns `[]` if the input is empty
- otherwise calls `self.model.encode(...)`
- converts the result to a plain Python list using `.tolist()`

### `embed_query(query: str) -> List[float]`

Encodes a single query by delegating to `embed_texts([query])[0]`.

## Example

```python
provider = SentenceTransformerEmbeddingProvider(
    model_name_or_path="all-MiniLM-L6-v2",
    normalize_embeddings=True,
)

doc_vectors = provider.embed_texts(["GraphRAG is useful.", "Neo4j stores graphs."])
query_vector = provider.embed_query("What is GraphRAG?")
```

## Advantages

- real semantic embeddings
- simple interface
- suitable for retrieval experiments and demos

## Limitations

- model loading cost
- external package dependency
- runtime performance depends on local hardware and model size
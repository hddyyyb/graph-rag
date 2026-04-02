# `infra.adapters.embedding_provider`

## Overview

This module provides `HashEmbeddingProvider`, a lightweight deterministic embedding adapter.

It is designed for early-stage development, offline testing, and environments where external embedding models or APIs are unavailable.

## Class

## `HashEmbeddingProvider`

### Purpose

`HashEmbeddingProvider` implements `EmbeddingProviderPort` and converts text into fixed-size numeric vectors using SHA-256 hashing.

It does **not** generate semantic embeddings. Instead, it produces stable pseudo-embeddings that are sufficient for:
- interface validation
- pipeline testing
- deterministic unit tests
- offline demos

## Constructor

### `__init__(dim: int = 32) -> None`

**Parameters**
- `dim`: output embedding dimension

**Instance Attributes**
- `dim: int` — size of each generated vector

## Methods

### `_hash_to_vec(s: str) -> List[float]`

Internal helper that:
1. hashes the input string with SHA-256
2. maps hash bytes into float values
3. expands or repeats values until `dim` is reached

**Input**
- `s`: source text

**Output**
- `List[float]` of length `dim`

### `embed_texts(texts: List[str]) -> List[List[float]]`

Generates one deterministic vector per input text.

**Input**
- `texts`: list of strings

**Output**
- list of embeddings

### `embed_query(query: str) -> List[float]`

Generates one deterministic vector for a query string.

**Input**
- `query`: query text

**Output**
- one embedding vector

## Example

```python
provider = HashEmbeddingProvider(dim=8)

texts = ["hello", "world"]
vectors = provider.embed_texts(texts)

query_vec = provider.embed_query("hello")
```

## Properties

### Advantages
- no external dependency
- no model loading
- fully deterministic
- fast and simple

### Limitations
- not semantically meaningful
- unsuitable for real retrieval quality
- only useful as a fake or bootstrap embedding backend

## Typical Role in the System

This adapter is commonly used when:
- the project is still validating architecture
- tests should not depend on model downloads
- a real embedding backend is not yet configured

## Replacement Path

A production system can replace this adapter with a real embedding provider without changing application-layer code, because both follow the same port-based contract.
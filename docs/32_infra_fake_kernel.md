# `infra.adapters.fake_kernel`

## Overview

This module provides `FakeKernel`, a minimal implementation of `RAGKernelPort`.

It is a testing adapter that records the latest query and retrieved contexts, then returns a predefined fixed answer.

## Class

## `FakeKernel`

### Purpose

`FakeKernel` is used to test the application layer without calling a real answer generation backend.

It helps verify:
- whether the query was passed correctly
- whether retrieved chunks were passed into the kernel
- whether the orchestration flow is working

## Constructor

### `__init__() -> None`

Initializes three fields:

- `last_query = ""`
- `last_chunks = []`
- `reply = "fake-answer"`

## Instance Attributes

- `last_query`: stores the latest query string received
- `last_chunks`: stores the latest contexts passed to the kernel
- `reply`: fixed answer returned by `generate_answer`

## Methods

### `generate_answer(query: str, contexts: List[RetrievedChunk])`

Stores the call inputs and returns the configured fake response.

**Inputs**
- `query`: user query string
- `contexts`: retrieved chunks

**Output**
- a string, usually `"fake-answer"`

## Example

```python
kernel = FakeKernel()

answer = kernel.generate_answer(
    query="What is GraphRAG?",
    contexts=[],
)

assert answer == "fake-answer"
assert kernel.last_query == "What is GraphRAG?"
assert kernel.last_chunks == []
```

## Why This Adapter Exists

A fake kernel is useful because it:
- isolates service-layer logic from generation logic
- makes tests deterministic
- avoids any dependency on LLMs or prompt construction

## Limitations

- no prompt building
- no language generation
- no grounding behavior
- only suitable for tests
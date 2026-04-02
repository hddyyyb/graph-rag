# LLM Port

## Overview

This file defines the `LLMPort`, which is the lowest-level abstraction for language model text generation in the GraphRAG system.

It represents a generic text generation interface:

- input: prompt string
- output: generated string

This port is usually used by a higher-level component such as a RAG kernel.

---

## Interface

```python
from __future__ import annotations

from typing import Protocol


class LLMPort(Protocol):
    def generate(self, prompt: str) -> str:
        ...
```

---

## Method

### `generate(prompt)`

Generates text from a prompt.

```python
def generate(self, prompt: str) -> str:
    ...
```

#### Parameters

- `prompt`: The input prompt string

#### Returns

- `str`: Generated output text

---

## Responsibility

`LLMPort` abstracts away the concrete language model backend.

Possible implementations include:

- fake test LLM
- local LLM server
- OpenAI API backend
- other third-party model providers

---

## Relationship to RAGKernelPort

`LLMPort` and `RAGKernelPort` are related, but they are not the same.

### `LLMPort`

A low-level model generation interface.

It only knows:

- prompt in
- text out

### `RAGKernelPort`

A higher-level RAG-oriented interface.

It knows:

- user query
- retrieved chunks
- answer generation workflow

In practice, a `RAGKernelPort` implementation may internally call an `LLMPort`.

---

## Why This Port Exists

The application layer should not directly depend on:

- OpenAI SDK
- local inference server APIs
- HTTP request details
- provider-specific response formats

Instead, it depends on this simple generation contract.

That makes the system:

- easier to test
- easier to swap backends
- cleaner in architecture

---

## Example Usage

```python
prompt = """
Answer the question based on the following context:

Context:
GraphRAG combines vector retrieval and graph retrieval.

Question:
What is GraphRAG?
"""

result = llm.generate(prompt)
```

---

## Typical Role in the System

```text
QueryService
  -> RAGKernelPort
      -> prompt construction
      -> LLMPort.generate(prompt)
      -> return model output
```

---

## Design Notes

This interface is intentionally minimal.

It does not expose:

- temperature
- max tokens
- stop sequences
- model name
- system/user role separation

Those concerns can be handled inside the concrete implementation or wrapped by a higher-level component.

This keeps the port stable and easy to use.

---

## Summary

`LLMPort` defines the generic text generation boundary for language model backends.

It keeps the application layer isolated from provider-specific model invocation details.
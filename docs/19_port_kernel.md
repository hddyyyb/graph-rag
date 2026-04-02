# RAG Kernel Port

## Overview

This file defines the `RAGKernelPort`, which is the abstraction for final answer generation in the GraphRAG system.

It represents the component responsible for turning:

- a user query
- a list of retrieved chunks

into:

- a final answer string

This port keeps the application layer independent from any specific answer-generation implementation.

---

## Interface

```python
from __future__ import annotations

from typing import List, Protocol

from graph_rag.domain.models import RetrievedChunk


class RAGKernelPort(Protocol):
    def generate_answer(self, query: str, contexts: List[RetrievedChunk]) -> str:
        ...
```

---

## Method

### `generate_answer(query, contexts)`

Generates the final answer based on the user query and retrieved context chunks.

```python
def generate_answer(self, query: str, contexts: List[RetrievedChunk]) -> str:
    ...
```

#### Parameters

- `query`: The user query string
- `contexts`: A list of retrieved chunks used as grounding context

#### Returns

- `str`: The final generated answer

---

## Responsibility

The `RAGKernelPort` sits at the boundary between:

- retrieval orchestration
- answer generation

It does not define how the answer is generated internally.  
That decision is delegated to the infrastructure layer.

Possible implementations may include:

- prompt-based LLM answer generation
- template-based summarization
- local model inference
- remote API generation

---

## Why This Port Exists

The main purpose of this port is to prevent the application layer from depending directly on a concrete LLM or generation strategy.

Without this abstraction, `QueryService` would need to know:

- how prompts are built
- how context is formatted
- which model is used
- how generation is invoked

With this port, the application layer simply says:

> Here is the query and the retrieved context. Please generate the answer.

---

## Example Usage

```python
answer = rag_kernel.generate_answer(
    query="What is GraphRAG?",
    contexts=[
        RetrievedChunk(
            doc_id="doc1",
            chunk_id="c1",
            text="GraphRAG combines vector retrieval and graph retrieval.",
            score=0.95,
            source="hybrid",
        )
    ],
)
```

---

## Typical Data Flow

```text
QueryService
  -> retrieve chunks
  -> call RAGKernelPort.generate_answer(query, contexts)
  -> receive final answer string
```

---

## Design Notes

This port is intentionally minimal.

It only exposes one method because its purpose is focused:

- consume query and context
- produce answer text

That simplicity makes the generation stage easy to replace and test.

---

## Summary

`RAGKernelPort` defines the answer-generation boundary of the system.

It allows the application layer to remain clean, testable, and independent from concrete generation implementations.
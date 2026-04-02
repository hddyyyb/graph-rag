# `infra.adapters.llamaindex_kernel`

## Overview

This module currently provides `SimpleKernel`, a minimal `RAGKernelPort` implementation.

Despite the filename, the implementation shown here is a deterministic placeholder kernel rather than a true LlamaIndex integration.

## Class

## `SimpleKernel`

### Purpose

`SimpleKernel` builds a readable answer directly from retrieved contexts.

It exists to make the RAG pipeline:
- testable
- explainable
- deterministic
- independent from real LLM infrastructure

This is useful in the early phase of system development.

## Methods

### `generate_answer(query: str, contexts: List[RetrievedChunk]) -> str`

Generates a simple text answer from the top retrieved chunks.

### Behavior

If there are no contexts, it returns a fallback message:

```python
"未检索到相关上下文。query={query}"
```

If contexts exist:
1. it keeps the top 3 chunks
2. converts each chunk into a short bullet line
3. truncates long snippets
4. returns a structured plain-text answer

## Output Style

The answer is a deterministic summary like:

```text
基于检索到的上下文，给出一个最小可用回答（Day2占位）：
- [vector] doc1/c0 score=0.911: ...
- [graph] doc1/c1 score=0.740: ...
```

## Why This Adapter Exists

It allows the system to validate:
- end-to-end query flow
- retrieval result passing
- answer construction

without depending on:
- prompt templates
- LLM APIs
- streaming
- external frameworks

## Limitations

- not a true LLM kernel
- not a true LlamaIndex integration
- fixed formatting
- no reasoning beyond string formatting

## Suggested Future Evolution

A future implementation in this file may:
- integrate LlamaIndex query pipelines
- add prompt templates
- support answer grounding and citations
- delegate generation to a configurable LLM backend
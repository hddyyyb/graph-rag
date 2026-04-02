# `infra.adapters.simple_rag_kernel`

## Overview

This module provides `SimpleRAGKernel`, an implementation of `RAGKernelPort` that delegates final answer generation to an injected `LLMPort`.

It is a bridge between retrieved chunk contexts and an LLM backend.

## Class

## `SimpleRAGKernel`

### Purpose

`SimpleRAGKernel` builds a grounded prompt from retrieved contexts and sends it to an LLM.

It is more realistic than a fake kernel because it:
- formats context explicitly
- limits the number of chunks
- delegates generation to a configurable LLM adapter

## Constructor

### `__init__(llm: LLMPort)`

**Parameters**
- `llm`: any adapter implementing `LLMPort`

**Instance Attributes**
- `llm`: injected LLM dependency

## Methods

### `generate_answer(query: str, contexts: List[RetrievedChunk]) -> str`

Builds a prompt and calls `self.llm.generate(prompt)`.

## Prompt Construction

The method formats up to 10 chunks as:

```text
[doc_id:chunk_id|source|score=...]
chunk text
```

Then wraps them into a prompt containing:
- assistant role description
- user question
- context section
- answer cue

## Prompt Template Shape

```text
你是一个严谨的企业级RAG助手。请仅根据给定上下文回答问题。

问题：{query}

上下文：
{context_text}

回答：
```

## Example

```python
kernel = SimpleRAGKernel(llm=FakeLLM())

answer = kernel.generate_answer(
    query="What does the graph store do?",
    contexts=retrieved_chunks,
)
```

## Advantages

- grounded prompt construction
- LLM backend remains pluggable
- easy to swap fake/local/OpenAI implementations

## Limitations

- prompt text is currently hard-coded
- no citation formatting in answer generation
- no structured output mode
- no streaming support
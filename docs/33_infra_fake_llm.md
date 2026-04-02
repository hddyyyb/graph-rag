# `infra.adapters.fake_llm`

## Overview

This module provides `FakeLLM`, a minimal implementation of `LLMPort`.

It records the latest prompt and always returns a fixed response string.

## Class

## `FakeLLM`

### Purpose

`FakeLLM` is a deterministic mock LLM adapter for tests.

It is useful when you want to verify:
- whether a prompt was constructed correctly
- whether an LLM was called
- whether the overall RAG answer pipeline is wired correctly

## Declaration Style

This class is implemented as a `dataclass`.

## Fields

- `reply: str = "fake-answer"`  
  The response returned by `generate`.

- `last_prompt: str = ""`  
  Stores the most recent prompt received.

## Methods

### `generate(prompt: str) -> str`

Stores the input prompt in `last_prompt` and returns `reply`.

**Input**
- `prompt`: prompt string

**Output**
- fixed string response

## Example

```python
llm = FakeLLM(reply="ok")

result = llm.generate("Explain GraphRAG.")
assert result == "ok"
assert llm.last_prompt == "Explain GraphRAG."
```

## Strengths

- deterministic
- zero dependency
- ideal for unit tests
- useful for verifying prompt content

## Limitations

- no real model behavior
- no inference
- no grounding
- no streaming or structured output
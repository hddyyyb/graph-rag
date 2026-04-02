# `infra.adapters.openai_llm`

## Overview

This module provides `OpenAILLM`, an `LLMPort` implementation backed by the OpenAI Responses API.

It is the hosted LLM adapter in the system and is intended for real answer generation.

## Class

## `OpenAILLM`

### Purpose

`OpenAILLM` sends prompts to an OpenAI model and returns the generated output text.

It allows the application layer to use a hosted LLM through the same interface used by fake or local LLM adapters.

## Declaration Style

This class is implemented as a `dataclass`.

## Fields

- `api_key: Optional[str] = None`  
  API key used when creating the OpenAI client

- `model: str = "gpt-5"`  
  Model name used for generation

- `instructions: str = "You are a helpful assistant."`  
  System-level instruction string

## Methods

### `generate(prompt: str) -> str`

Creates an OpenAI client and calls the Responses API.

### Request Pattern

```python
res = client.responses.create(
    model=self.model,
    instructions=self.instructions,
    input=prompt,
)
```

### Return Value

The method returns:

```python
(res.output_text or "").strip()
```

So the output is always a clean string.

## Example

```python
llm = OpenAILLM(
    api_key="your-api-key",
    model="gpt-5",
    instructions="Answer using only the provided context.",
)

answer = llm.generate("Explain GraphRAG.")
```

## Design Notes

- imports `OpenAI` lazily inside the method
- this avoids import-time failures in environments where the OpenAI package is not installed
- helps keep offline tests lightweight

## Advantages

- real hosted generation backend
- simple adapter surface
- compatible with the same `LLMPort` used by fake and local implementations

## Limitations

- depends on network access
- depends on API credentials
- current implementation does not include retries, timeout customization, or structured error handling
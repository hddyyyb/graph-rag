# `infra.adapters.local_llm`

## Overview

This module provides `LocalLLM`, a local HTTP-based implementation of `LLMPort`.

It sends prompts to a locally hosted model server using a simple JSON POST request.

The default target matches the Ollama-style `/api/generate` endpoint.

## Class

## `LocalLLM`

### Purpose

`LocalLLM` enables the system to use a local large language model without changing application-layer logic.

It is useful for:
- local development
- offline demos
- experiments with self-hosted LLMs

## Declaration Style

This class is implemented as a `dataclass`.

## Fields

- `base_url: str = "http://localhost:11434"`  
  Base URL of the local model server

- `model: str = "llama3"`  
  Model name sent in the request body

- `timeout_s: float = 60.0`  
  Request timeout in seconds

## Methods

### `generate(prompt: str) -> str`

Sends a JSON POST request to:

```python
f"{base_url.rstrip('/')}/api/generate"
```

Request payload:

```json
{
  "model": "llama3",
  "prompt": "your prompt here",
  "stream": false
}
```

Then:
1. reads the JSON response
2. extracts `response`
3. strips whitespace
4. returns the final string

## Example

```python
llm = LocalLLM(
    base_url="http://localhost:11434",
    model="llama3",
)

answer = llm.generate("Explain GraphRAG in one paragraph.")
```

## Expected Response Format

The adapter assumes a response shape similar to:

```json
{
  "response": "Generated answer text"
}
```

## Advantages

- works with local model servers
- avoids external API dependence
- keeps the system pluggable

## Limitations

- depends on server availability
- no retry logic
- no streaming support
- no advanced error handling in the current implementation
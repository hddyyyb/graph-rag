# Text Utilities

## Overview

This module provides basic text processing utilities used across the GraphRAG system.

Currently, it focuses on:

- keyword extraction
- lightweight text normalization
- stopword filtering

The core function is:

'''python
extract_terms(text: str) -> List[str]
'''

It converts raw text into a **clean list of terms** that can be used in:

- graph construction
- graph retrieval
- term-based indexing

:contentReference[oaicite:0]{index=0}

---

## Design Philosophy

This module intentionally implements a **minimal and fast baseline** for term extraction.

Goals:

- simple
- deterministic
- dependency-free
- fast enough for ingestion pipeline

It is **not designed to be linguistically perfect**, but to provide:

👉 a stable foundation for GraphRAG term-based retrieval

---

## STOPWORDS

'''python
STOPWORDS = {
    "the", "a", "an", "is", "are", "of", "to", "and", "or", "in", "on", "for",
    "with", "by", "as", "at", "from", "that", "this"
}
'''

### Purpose

- remove low-information words
- improve signal quality
- reduce noise in graph construction

These are common English function words that:

- appear frequently
- carry little semantic meaning

:contentReference[oaicite:1]{index=1}

---

## `extract_terms`

### Signature

'''python
def extract_terms(text: str) -> List[str]
'''

---

## Processing Pipeline

The function follows a simple pipeline:

'''text
Input Text
    ↓
Lowercase
    ↓
Regex Tokenization
    ↓
Filter (length / stopwords)
    ↓
Deduplication
    ↓
Output Terms
'''

---

## Step-by-step Breakdown

### 1. Empty check

'''python
if not text:
    return []
'''

---

### 2. Lowercase + Tokenization

'''python
tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
'''

### Behavior

- converts text to lowercase
- extracts tokens using regex

### Regex meaning

'''text
[a-zA-Z0-9_]+
'''

Matches:

- letters
- numbers
- underscore
- continuous sequences only

Example:

'''text
"Graph-RAG v2.0!" → ["graph", "rag", "v2", "0"]
'''

:contentReference[oaicite:2]{index=2}

---

### 3. Filtering

'''python
if len(token) < 2:
    continue
if token in STOPWORDS:
    continue
'''

Removes:

- very short tokens (length < 2)
- stopwords

---

### 4. Deduplication

'''python
seen = set()
if token in seen:
    continue
seen.add(token)
'''

Ensures:

- each term appears only once
- preserves first occurrence order

---

### 5. Output

'''python
return results
'''

Returns:

- list of unique, cleaned terms

:contentReference[oaicite:3]{index=3}

---

## Example

### Input

'''text
"FastAPI is a modern web framework for building APIs with Python"
'''

### Output

'''python
["fastapi", "modern", "web", "framework", "building", "apis", "python"]
'''

---

## Role in GraphRAG

This function is used in:

### 1. Graph Ingestion

'''text
Chunk text
    ↓
extract_terms()
    ↓
ChunkGraphRecord(terms=...)
    ↓
GraphStore
'''

---

### 2. Graph Retrieval

'''text
Query
    ↓
extract_terms()
    ↓
GraphStore.search(terms)
'''

---

## Limitations (Important)

This implementation is intentionally simple and has several limitations:

### 1. No Chinese support

- only supports `[a-zA-Z0-9_]`
- Chinese text will not be tokenized correctly

### 2. No stemming / lemmatization

- "running" ≠ "run"
- no normalization of word forms

### 3. No Named Entity Recognition (NER)

- cannot detect entities like:
  - "New York"
  - "Graph Neural Network"

### 4. No phrase extraction

- "graph database" → split into:
  - "graph"
  - "database"

instead of one semantic unit

### 5. No semantic filtering

- purely rule-based
- no TF-IDF / embedding-based filtering

:contentReference[oaicite:4]{index=4}

---

## Suggested Improvements

The file itself already hints at future upgrades:

### 1. NLP Libraries

- NLTK
- spaCy

Add:

- lemmatization
- stemming
- POS tagging

---

### 2. Phrase Extraction

'''text
"graph database" → "graph_database"
'''

- improves graph quality
- better semantic representation

---

### 3. TF-IDF Filtering

- remove low-importance tokens
- keep high-signal terms

---

### 4. Embedding-based Terms

- cluster tokens
- semantic grouping
- context-aware extraction

---

## Design Trade-off

| Aspect | Current Choice | Reason |
|------|--------|------|
| Accuracy | Low | Keep simple |
| Speed | High | Regex only |
| Dependency | None | Easy setup |
| Determinism | High | No randomness |

---

## When to Use

Use this module when:

- building graph from chunks
- extracting query terms
- running baseline GraphRAG
- writing unit tests

---

## When NOT to Use

Avoid this approach when:

- dealing with multilingual text
- requiring semantic understanding
- building production-grade NLP pipelines
- handling entity-heavy documents

---

## Summary

`extract_terms` is a **baseline keyword extraction utility** that:

- converts raw text into structured term lists
- enables graph construction and retrieval
- prioritizes simplicity and speed over linguistic accuracy

It serves as a **foundation layer** that can later be upgraded into a full NLP pipeline without changing the system architecture.

:contentReference[oaicite:5]{index=5}
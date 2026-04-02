# Graph Debug Models

## Overview

This file defines the structured debug models used by the graph retrieval subsystem.

These models make graph retrieval:

- explainable
- debuggable
- observable
- easier to test across backends

They are especially important after the retrieval pipeline evolves from simple count-based matching to more fine-grained weighted scoring.

---

## Why These Models Exist

Graph retrieval is not only about returning chunks.  
It also needs to explain:

- which query terms were used
- which expanded terms were generated
- which expanded terms actually contributed to chunk scoring
- how much direct matching contributed
- how much expanded matching contributed
- what final score each chunk received

This file provides a structured representation for all of that.

---

## Technology Choice

Unlike some other domain files that use `dataclass`, this file uses **Pydantic models**:

```python
from pydantic import BaseModel, Field
```

This choice is useful because debug structures often benefit from:

- clear typed validation
- convenient serialization
- predictable default values
- easier API/debug payload export

---

## Classes

### GraphExpandedTermDebug

Represents a query expansion candidate.

```python
class GraphExpandedTermDebug(BaseModel):
    query_term: str
    expanded_term: str
    weight: float
```

#### Fields

- `query_term`: Original query term
- `expanded_term`: Expanded term discovered from the graph
- `weight`: Expansion weight associated with the relation

#### Meaning

This model describes the **candidate expansion space**.

It answers the question:

> For a given query term, which related graph terms were expanded, and with what weight?

#### Example

```json
{
  "query_term": "llm",
  "expanded_term": "rag",
  "weight": 3.0
}
```

---

### GraphExpandedHitDebug

Represents an expanded term that actually contributed to a chunk score.

```python
class GraphExpandedHitDebug(BaseModel):
    query_term: str
    expanded_term: str
    weight: float
    contribution: float
```

#### Fields

- `query_term`: Original query term
- `expanded_term`: Expanded term that matched the chunk
- `weight`: Expansion weight
- `contribution`: Actual contribution of this expansion to the chunk score

#### Meaning

This model is more specific than `GraphExpandedTermDebug`.

- `GraphExpandedTermDebug` describes what the system expanded
- `GraphExpandedHitDebug` describes what actually hit a chunk and changed its score

#### Example

```json
{
  "query_term": "llm",
  "expanded_term": "rag",
  "weight": 3.0,
  "contribution": 1.5
}
```

---

### GraphChunkDebug

Represents debug information for a single retrieved chunk.

```python
class GraphChunkDebug(BaseModel):
    chunk_id: str
    doc_id: str
    direct_terms: List[str] = Field(default_factory=list)
    expanded_hits: List[GraphExpandedHitDebug] = Field(default_factory=list)
    direct_hit_count: int = 0
    expanded_hit_count: int = 0
    direct_score: float = 0.0
    expanded_score: float = 0.0
    score: float = 0.0
```

#### Fields

- `chunk_id`: Retrieved chunk ID
- `doc_id`: Parent document ID
- `direct_terms`: Direct query terms matched by the chunk
- `expanded_hits`: Expanded-term hits that contributed to the chunk
- `direct_hit_count`: Number of direct matches
- `expanded_hit_count`: Number of expanded matches
- `direct_score`: Score contributed by direct hits
- `expanded_score`: Score contributed by expanded hits
- `score`: Final total chunk score

#### Meaning

This model explains:

- which terms matched the chunk directly
- which expanded terms matched the chunk indirectly
- how each part contributed to the final ranking

This makes the chunk-level scoring pipeline transparent.

#### Example

```json
{
  "chunk_id": "chunk_01",
  "doc_id": "doc_001",
  "direct_terms": ["llm"],
  "expanded_hits": [
    {
      "query_term": "llm",
      "expanded_term": "rag",
      "weight": 3.0,
      "contribution": 1.5
    }
  ],
  "direct_hit_count": 1,
  "expanded_hit_count": 1,
  "direct_score": 1.0,
  "expanded_score": 1.5,
  "score": 2.5
}
```

---

### GraphSearchDebug

Represents the full debug payload for one graph retrieval request.

```python
class GraphSearchDebug(BaseModel):
    query: str = ""
    direct_terms: List[str] = Field(default_factory=list)
    expanded_terms: List[GraphExpandedTermDebug] = Field(default_factory=list)
    chunks: List[GraphChunkDebug] = Field(default_factory=list)
    weights: Dict[str, float] = Field(default_factory=dict)
    scoring_formula: str = ""
    meta: Dict[str, object] = Field(default_factory=dict)
```

#### Fields

- `query`: Original input query
- `direct_terms`: Direct terms extracted from the query
- `expanded_terms`: All expanded candidate terms
- `chunks`: Per-chunk debug breakdown
- `weights`: Runtime scoring weights
- `scoring_formula`: Human-readable scoring formula
- `meta`: Arbitrary extra debug metadata

#### Meaning

This model gives a system-level explanation of graph retrieval.

It allows developers to inspect:

- the original query
- direct and expanded term signals
- per-chunk score breakdowns
- runtime scoring configuration
- extra diagnostic information

#### Example

```json
{
  "query": "llm retrieval",
  "direct_terms": ["llm", "retrieval"],
  "expanded_terms": [
    {
      "query_term": "llm",
      "expanded_term": "rag",
      "weight": 3.0
    }
  ],
  "chunks": [],
  "weights": {
    "direct_hit_weight": 1.0,
    "expanded_hit_weight": 0.5
  },
  "scoring_formula": "score = direct_count * direct_hit_weight + sum(weight * expanded_hit_weight)",
  "meta": {
    "backend": "neo4j"
  }
}
```

---

### GraphSearchResult

Represents the structured output of graph retrieval.

```python
class GraphSearchResult(BaseModel):
    hits: List[RetrievedChunk] = Field(default_factory=list)
    debug: GraphSearchDebug = Field(default_factory=GraphSearchDebug)
```

#### Fields

- `hits`: Retrieved chunk list
- `debug`: Full graph retrieval debug payload

#### Meaning

This is the final graph retrieval result object.

It bundles together:

- the actual retrieval hits
- the full explanation of how those hits were produced

---

## Relationship Between the Models

The hierarchy can be understood like this:

```text
GraphSearchResult
├── hits: List[RetrievedChunk]
└── debug: GraphSearchDebug
    ├── direct_terms
    ├── expanded_terms: List[GraphExpandedTermDebug]
    └── chunks: List[GraphChunkDebug]
         └── expanded_hits: List[GraphExpandedHitDebug]
```

---

## Expanded Terms vs Expanded Hits

A common point of confusion is the difference between:

- `expanded_terms`
- `expanded_hits`

### expanded_terms

This is the **global expansion candidate list** for the query.

It answers:

> Which related terms were expanded from the query?

### expanded_hits

This is the **chunk-specific matched expansion list**.

It answers:

> Which expanded terms actually matched this chunk and contributed to its score?

So:

- `expanded_terms` is query-level candidate expansion info
- `expanded_hits` is chunk-level scoring contribution info

---

## Engineering Value

These debug models provide several practical benefits.

### 1. Explainability

Developers can understand why a chunk ranked highly.

### 2. Backend consistency testing

The same debug structure can be compared across:

- in-memory graph backend
- Neo4j graph backend

### 3. Safer iteration

Scoring upgrades become easier because score breakdowns are explicit.

### 4. Better observability

The retrieval pipeline becomes inspectable during development and debugging.

---

## Example Usage

```python
debug = GraphSearchDebug(
    query="llm retrieval",
    direct_terms=["llm", "retrieval"],
    expanded_terms=[
        GraphExpandedTermDebug(
            query_term="llm",
            expanded_term="rag",
            weight=3.0,
        )
    ],
    chunks=[
        GraphChunkDebug(
            chunk_id="chunk_01",
            doc_id="doc_001",
            direct_terms=["llm"],
            expanded_hits=[
                GraphExpandedHitDebug(
                    query_term="llm",
                    expanded_term="rag",
                    weight=3.0,
                    contribution=1.5,
                )
            ],
            direct_hit_count=1,
            expanded_hit_count=1,
            direct_score=1.0,
            expanded_score=1.5,
            score=2.5,
        )
    ],
    weights={
        "direct_hit_weight": 1.0,
        "expanded_hit_weight": 0.5,
    },
    scoring_formula="score = direct_count * direct_hit_weight + sum(weight * expanded_hit_weight)",
    meta={"backend": "neo4j"},
)
```

---

## Summary

This file defines the explainability layer of graph retrieval:

- `GraphExpandedTermDebug`: expanded candidate terms
- `GraphExpandedHitDebug`: chunk-level expanded scoring contributions
- `GraphChunkDebug`: per-chunk scoring breakdown
- `GraphSearchDebug`: full graph retrieval debug payload
- `GraphSearchResult`: hits + debug bundle

Together, these models make the graph retrieval pipeline structured, transparent, and testable.
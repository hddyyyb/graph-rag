# `infra.adapters.in_memory_graph_store`

## Overview

This module provides `InMemoryGraphStore`, an in-memory graph retrieval backend implementing `GraphStorePort`.

It supports:
- chunk graph ingestion
- term indexing
- co-occurrence graph construction
- direct term retrieval
- 1-hop query expansion
- edge-weight-aware graph scoring
- explainable debug payload generation

This adapter is a memory-based reference implementation for graph retrieval logic.

## Core Idea

The store models retrieval in two channels:

1. **Direct hits**
   - exact query-term matches against chunk terms

2. **Expanded hits**
   - 1-hop neighbor terms expanded from the term co-occurrence graph

The final score is:

```python
score = direct_hit_count * direct_hit_weight + sum(expanded_edge_weight * expanded_hit_weight)
```

## Class

## `InMemoryGraphStore`

### Constructor

```python
InMemoryGraphStore(
    expand_per_term_limit: int = 2,
    direct_hit_weight: float = 1.0,
    expanded_hit_weight: float = 0.5,
    max_expanded_terms: int = 10,
)
```

### Constructor Parameters

- `expand_per_term_limit`: maximum number of neighbor terms expanded per direct query term
- `direct_hit_weight`: score contribution of each distinct direct match
- `expanded_hit_weight`: scaling factor for expanded hits
- `max_expanded_terms`: global upper bound for expanded term count

## Internal State

### Main retrieval structures

- `chunk_store: Dict[str, RetrievedChunk]`  
  Stores chunk content keyed by `chunk_id`

- `term_to_chunk_ids: Dict[str, Set[str]]`  
  Inverted index from term to matching chunk ids

- `term_graph: Dict[str, Dict[str, int]]`  
  Term co-occurrence graph with weights

### Optional graph-like structures

- `nodes_by_name: Dict[str, GraphNode]`
- `edges_by_pair: Dict[tuple[str, str], GraphEdge]`
- `chunk_terms: Dict[str, Set[str]]`
- `doc_to_chunk_ids: Dict[str, Set[str]]`

### Debug state

- `_last_debug: Optional[Dict[str, Any]]`

## Public Methods

### `get_last_debug() -> Optional[Dict[str, Any]]`

Returns the latest graph retrieval debug payload.

### `upsert_chunk_graphs(records: List[ChunkGraphRecord]) -> None`

Ingests chunk-level graph records.

For each record:
1. stores a `RetrievedChunk`
2. extracts or reuses terms
3. builds term-to-chunk index
4. updates term co-occurrence graph

### `search(query: str, top_k: int) -> List[RetrievedChunk]`

Executes graph retrieval.

Pipeline:
1. reset debug state
2. validate query and `top_k`
3. extract direct terms
4. expand terms with weights
5. collect direct chunk hits
6. collect expanded weighted chunk hits
7. compute scores
8. sort and return top results
9. save debug payload

## Scoring Model

### Direct score

```python
direct_score = direct_hit_count * direct_hit_weight
```

### Expanded score

```python
expanded_score = sum(contribution_i)
contribution_i = edge_weight * expanded_hit_weight
```

### Final score

```python
score = direct_score + expanded_score
```

## Important Internal Methods

### `_empty_debug_payload(query: str) -> Dict[str, Any]`
Creates a standard empty debug payload.

### `_build_debug_payload(...) -> Dict[str, Any]`
Builds structured explainable debug output for the latest search.

### `_index_chunk_terms(record, terms) -> None`
Indexes terms into the inverted term-to-chunk structure and creates graph nodes.

### `_update_term_cooccurrence(terms) -> None`
Updates the weighted co-occurrence graph and graph edges.

### `_expand_terms_with_weights(direct_terms) -> list[dict[str, Any]]`
Expands each direct term into ranked 1-hop neighbors.

### `_collect_chunk_hits(terms) -> dict[str, set[str]]`
Finds exact direct matches.

### `_collect_chunk_weighted_hits(expanded_terms) -> dict[str, list[dict[str, Any]]]`
Finds expanded matches and computes contribution values.

### `_build_retrieved_chunks(...) -> list[RetrievedChunk]`
Calculates scores, builds result objects, sorts, and trims to `top_k`.

## Debug Payload Structure

The stored debug object contains:

- `query`
- `direct_terms`
- `expanded_terms`
- `chunks`
- `weights`
- `scoring_formula`
- `meta`

Example shape:

```json
{
  "query": "rag graph",
  "direct_terms": ["graph", "rag"],
  "expanded_terms": [
    {
      "query_term": "rag",
      "expanded_term": "retrieval",
      "weight": 3.0
    }
  ],
  "chunks": [
    {
      "chunk_id": "c1",
      "doc_id": "doc1",
      "direct_terms": ["graph"],
      "expanded_hits": [
        {
          "query_term": "rag",
          "expanded_term": "retrieval",
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
  ]
}
```

## Strengths

- simple and transparent
- easy to test
- fully explainable
- useful as the reference graph retrieval backend

## Limitations

- in-memory only
- not persistent
- no multi-hop expansion
- term-based rather than entity-based graph modeling
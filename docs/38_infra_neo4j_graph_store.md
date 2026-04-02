# `infra.adapters.neo4j_graph_store`

## Overview

This module provides `Neo4jGraphStore`, a Neo4j-backed implementation of `GraphStorePort`.

It persists chunk-term graphs in Neo4j and performs graph retrieval with:
- direct term matching
- 1-hop term expansion
- weighted expanded scoring
- explainable debug output

Its ranking logic is intentionally aligned with the in-memory graph store.

## Retrieval Model

The store uses two retrieval channels.

### 1. Direct hits

A chunk receives direct score based on how many distinct query terms it matches:

```python
direct_score = direct_hit_count * direct_hit_weight
```

### 2. Expanded hits

Query terms are expanded through `CO_OCCURS_WITH` relationships.
Each expanded hit contributes:

```python
contribution = edge_weight * expanded_hit_weight
```

The expanded score is the sum of all contributions.

### 3. Final score

```python
score = direct_score + expanded_score
```

## Class

## `Neo4jGraphStore`

### Constructor

```python
Neo4jGraphStore(
    driver: Driver,
    database: str | None = None,
    ensure_schema_on_init: bool = True,
    expand_per_term_limit: int = 2,
    direct_hit_weight: float = 1.0,
    expanded_hit_weight: float = 0.5,
    max_expanded_terms: int = 10,
)
```

### Constructor Parameters

- `driver`: Neo4j driver instance
- `database`: target Neo4j database name
- `ensure_schema_on_init`: whether to create constraints on startup
- `expand_per_term_limit`: max expansion candidates per direct term
- `direct_hit_weight`: direct hit score multiplier
- `expanded_hit_weight`: expanded hit score multiplier
- `max_expanded_terms`: global max expanded term count

### Instance Attributes

- `driver`
- `database`
- `expand_per_term_limit`
- `direct_hit_weight`
- `expanded_hit_weight`
- `max_expanded_terms`
- `_last_debug`

## Graph Schema

The store uses these node and relationship types:

### Nodes
- `Chunk`
- `Term`

### Relationships
- `(:Chunk)-[:MENTIONS]->(:Term)`
- `(:Term)-[:CO_OCCURS_WITH]->(:Term)`

### Constraints
- `Chunk.chunk_id` is unique
- `Term.name` is unique

## Public Methods

### `get_last_debug() -> Optional[Dict[str, Any]]`
Returns the latest graph retrieval debug payload.

### `upsert_chunk_graphs(records: List[ChunkGraphRecord]) -> None`
Writes chunk graph records into Neo4j.

For each record:
1. compute normalized terms
2. remove stale co-occurrence contribution for old terms
3. delete old `MENTIONS` edges
4. upsert chunk node
5. rebuild `MENTIONS`
6. rebuild `CO_OCCURS_WITH` weights

### `search(query: str, top_k: int) -> List[RetrievedChunk]`
Runs graph search against Neo4j.

Pipeline:
1. validate query
2. extract direct terms
3. expand terms using Neo4j graph
4. query direct chunk hits
5. query expanded chunk hits
6. merge and rank results
7. store debug output

### `close() -> None`
Closes the underlying Neo4j driver.

## Important Internal Methods

### Schema
- `_ensure_schema()`

### Write transaction
- `_upsert_one_record_tx(...)`

### Search transactions
- `_search_chunks_by_terms_tx(...)`
- `_expand_terms_tx(...)`
- `_search_direct_hits_tx(...)`
- `_search_expanded_hits_tx(...)`

### Merge and ranking
- `_merge_rank_results(...)`

### Term normalization
- `_get_terms_from_record(...)`
- `_expand_terms_with_weights(...)`
- `_normalize_terms(...)`
- `_strip_token(...)`

## Debug Payload

The debug payload contains:
- `query`
- `direct_terms`
- `expanded_terms`
- `chunks`
- `weights`
- `scoring_formula`
- `meta`

Example structure:

```json
{
  "query": "database index",
  "direct_terms": ["database", "index"],
  "expanded_terms": [
    {
      "query_term": "database",
      "expanded_term": "sql",
      "weight": 3.0
    }
  ],
  "chunks": [
    {
      "chunk_id": "c1",
      "doc_id": "doc1",
      "direct_terms": ["database"],
      "expanded_hits": [
        {
          "query_term": "database",
          "expanded_term": "sql",
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

- persistent graph backend
- Cypher-based retrieval and expansion
- aligned with in-memory graph semantics
- explainable graph scoring

## Limitations

- no multi-hop traversal
- still term-based rather than entity-based
- current implementation focuses on correctness and clarity rather than maximum query efficiency
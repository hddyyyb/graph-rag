# Scripts

This directory contains utility scripts for debugging, evaluation, analysis, and engineering experiments.

Scripts are typically used as a developer experimentation area rather than part of the formal system architecture.

Typical characteristics:

- rapid validation
- temporary experiments
- debugging
- exploratory analysis
- one-off tools

These scripts do not represent core production capabilities.
Instead, they support the engineering research and development process.

---

## Script Categories

### 1. Shared Helpers

#### helpers.py

Shared factory helpers used by other scripts.

Main utilities:

- `build_query_service()`
- `build_ingest_service()`

Purpose:

- avoid duplicated service construction logic
- keep script setup consistent
- provide default in-memory components for debugging and evaluation

Notes:

- scripts may override vector store, graph store, embedder, and chunker
- defaults are intended for local experiments only

---

### 2. Vector Backend Analysis

#### compare_vector_backends.py

Compare SQLite vs Qdrant vector store behavior.

Purpose:

- run the same evaluation dataset on different vector backends
- compare Recall@K / MRR
- compare latency
- verify VectorStore abstraction consistency

Use this script when analyzing:

- SQLite vs Qdrant retrieval behavior
- backend switching correctness
- vector retrieval result stability
- production-oriented vector database upgrade impact

Requirements:

- Qdrant should be running locally when testing Qdrant
- SQLite may use an in-memory database for quick comparison

---

#### inspect_qdrant_behavior.py

Inspect Qdrant retrieval behavior.

Purpose:

- observe Qdrant top_k behavior
- inspect score distribution
- check repeated-query stability
- test edge cases such as unrelated queries

Use this script when analyzing:

- Qdrant ranking stability
- score ranges
- empty or weak-match query behavior
- top_k sensitivity

Notes:

- this script focuses on vector retrieval only
- graph retrieval is disabled in this script

---

### 3. Hybrid Retrieval Analysis

#### analyze_fusion_behavior.py

Analyze hybrid fusion behavior between vector retrieval and graph retrieval.

Purpose:

- compare vector-only, graph-only, and hybrid retrieval
- inspect how fusion_alpha / fusion_beta affect ranking
- observe whether hybrid retrieval is vector-dominant or graph-dominant
- support before/after comparison for fusion scoring changes

Use this script when analyzing:

- fusion weight behavior
- score normalization impact
- hybrid ranking changes
- false positives / false negatives across retrieval modes

Typical output:

- Recall@K
- MRR
- false negatives
- false positives
- retrieval_debug details
- ranking comparison under different alpha / beta settings

---

### 4. Graph Scoring Debugging

#### inspect_graph_scoring_case.py

Inspect graph retrieval scoring behavior on controlled cases.

Purpose:

- analyze direct term hits
- analyze expanded term hits
- inspect graph score breakdown
- inspect expansion contribution cap behavior
- compare InMemoryGraphStore and Neo4jGraphStore behavior

Use this script when analyzing:

- graph centrality bias
- noisy graph expansion
- direct vs expanded score contribution
- expansion_score_cap effect
- InMemory / Neo4j consistency

Current debug output sections:

- Retrieval Debug Summary
- Ranking Preview
- Scoring Overview
- Final Results
- Graph Debug

Supported backends:

```text
--backend in_memory
--backend neo4j
--backend both
```

Notes:

- Neo4j mode checks connectivity before running
- Neo4j data may be cleared before each run to avoid stale results
- this script uses graph-only retrieval by default

---

## Debugging Workflow

Recommended usage order:

1. Use inspect_graph_scoring_case.py when a graph ranking result looks suspicious.
2. Use analyze_fusion_behavior.py when hybrid ranking is hard to explain.
3. Use compare_vector_backends.py when validating SQLite vs Qdrant behavior.
4. Use inspect_qdrant_behavior.py when investigating Qdrant-specific score or top_k behavior.

---

## Notes
- scripts may use dedicated Qdrant collections, such as graphrag_eval
- these collections are for testing only
- production collections should be managed separately
- script outputs are intended for engineering inspection, not stable API contracts
- scripts may evolve faster than core application code
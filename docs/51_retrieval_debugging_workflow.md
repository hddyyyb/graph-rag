# Retrieval Debugging Workflow

## 1. Purpose

This document defines a standard workflow for analyzing retrieval failures in the GraphRAG system.

The goal is not to change retrieval logic, but to make ranking behavior observable, explainable, and reproducible.

## 2. When to Use This Workflow

Use this workflow when:
- the expected chunk is missing
- the expected chunk ranks too low
- graph retrieval introduces noisy results
- hybrid ranking is dominated by one retrieval source
- before/after scoring changes need comparison

## 3. Debugging Order

1. Inspect query and effective options
2. Inspect vector retrieval results
3. Inspect graph retrieval results
4. Inspect graph scoring breakdown
5. Inspect fusion scores
6. Inspect normalized scores
7. Inspect final merged ranking
8. Inspect citations and false negatives

## 4. Retrieval Debug Structure

`retrieval_debug` is organized into several layers.

### summary

High-level query execution summary.

Use it to quickly check:

- retrieval mode
- vector / graph enabled status
- vector_count / graph_count
- fused_count / final_count
- postprocess_removed_count
- normalization status

### ranking_preview

Compact final ranking view.

Use it to check:

- final rank
- whether a chunk comes from vector, graph, or both
- raw score vs effective score
- final_score used for ranking

Important:

- `raw_*_score` means score before normalization
- `effective_*_score` means score actually used by fusion
- `final_score` means score after fusion weights

### scoring_overview

Scoring configuration summary.

Use it to check:

- fusion alpha / beta
- normalization status
- graph scoring weights
- expansion_score_cap
- whether expansion cap was triggered

### vector / graph

Raw retrieval-level debug information.

Use these sections when you need to inspect vector or graph retrieval behavior before fusion.

### fusion

Fusion-level debug information.

Use it when ranking behavior is hard to explain from `ranking_preview` alone.

### fused / final

These two sections clarify retrieval stages:

- `fused`: chunks after fusion and before post-processing
- `final`: chunks after post-processing and used for answer generation / citations

### timings / stats

Runtime and numerical summary information.

Use these sections for performance or count-level diagnosis.

## 5. Failure Types

### Missing Recall

The relevant chunk does not appear in vector, graph, or hybrid results.

Possible causes:
- chunk boundary problem
- term extraction mismatch
- vector similarity too weak
- graph expansion failed

### Ranking Failure

The relevant chunk is retrieved but ranks too low.

Possible causes:
- topic chunk dominance
- graph centrality bias
- score scale imbalance
- expansion contribution too high

### Noisy Graph Expansion

Graph retrieval returns chunks through weak or high-frequency expanded terms.

Possible causes:
- broad co-occurrence edges
- stopword-like terms
- high-degree term nodes
- insufficient expansion cap

### Fusion Imbalance

Hybrid ranking behaves too similarly to vector-only or graph-only retrieval.

Possible causes:
- alpha / beta setting
- normalization disabled
- raw score scale mismatch
# Evaluation: Case-Level Error Analysis

Traditional evaluation metrics such as Recall@K and MRR only provide aggregate performance,
but do not reveal *why* retrieval succeeds or fails at the query level.

To address this, we introduce case-level error analysis.

## Overview

This document describes the case-level error analysis capability added to the GraphRAG evaluation pipeline. It explains the methodology, what each diagnostic field captures, and what the benchmark results reveal about the relative strengths of vector, graph, and hybrid retrieval on a small English-language dataset.

The analysis was produced by `src/graph_rag/evaluation/run_case_analysis.py`, which runs the full evaluation pipeline against a fixed test corpus and prints per-query diagnostic output for all three retrieval modes.

---

## Method

### Corpus and Queries

The benchmark uses a short descriptive passage about a fictional location called Meteor City (~700 characters). The document is ingested as `doc1` and chunked with `RecursiveChunker(chunk_size=100, chunk_overlap=0)`, producing seven sequential chunks (`doc1#0` through `doc1#6`).

Three evaluation queries are defined, each with a manually annotated set of relevant chunk IDs:

| Query | Relevant Chunks |
|---|---|
| What is Meteor City like in the eyes of outsiders? | `doc1#1`, `doc1#2` |
| How do people in Meteor City primarily survive? | `doc1#3`, `doc1#4` |
| What is Meteor City truly like? | `doc1#6`, `doc1#7` |

Each query is evaluated under three retrieval modes — **vector**, **graph**, and **hybrid** — at `k=3`.

### Metrics

- **Recall@K**: fraction of relevant chunks found within the top-K retrieved results.
- **MRR (Mean Reciprocal Rank)**: reciprocal of the rank position of the first relevant result; measures how early the system surfaces a correct answer.

Both metrics are computed per query and averaged across the dataset to produce summary statistics.

### Case-Level Diagnostic Fields

In addition to aggregate metrics, each `EvalResult` now carries four fields for per-query error inspection:

| Field | Description |
|---|---|
| `relevant_chunk_ids` | Ground-truth chunk IDs for this query |
| `relevant_ranks` | 1-based rank of each relevant chunk in the retrieved list; `None` if not retrieved |
| `false_negatives` | Relevant chunks that were not retrieved — missed recalls |
| `false_positives` | Retrieved chunks that are not relevant — noise in the result set |

These fields allow a human reviewer to inspect exactly which chunks were missed and which irrelevant chunks displaced them, without rerunning any retrieval logic.

---

## Case-Level Analysis

### What False Negatives Reveal

A **false negative** (FN) occurs when a chunk that should have been retrieved is absent from the result list. In a retrieval system, FNs represent failures of coverage: the system retrieved `k` results, but the correct answer was not among them.

FNs are the primary driver of low Recall@K. When a query has multiple relevant chunks and only one is retrieved, the other appears as a false negative. This commonly happens when:

- The query uses a different vocabulary than the chunk text (vector embedding mismatch), or
- The chunk lacks the specific terms the graph indexer extracted (graph coverage gap).

### What False Positives Reveal

A **false positive** (FP) occurs when a retrieved chunk is not relevant to the query. FPs do not directly reduce Recall@K (which only measures hits among the top-K), but they indicate noise in the ranked list: slots occupied by irrelevant chunks could have been used for missed relevant ones.

In this benchmark, FPs typically appear when a chunk shares surface-level keywords with the query but does not contain the answer. Graph retrieval introduces FPs when expanded synonym terms over-match on unrelated passages.

This reflects a classic recall–precision trade-off:
graph expansion improves coverage but introduces additional noise.

### Observed Patterns Across the Three Queries

**Graph retrieval** performed strongest on this benchmark. Its direct term matching captures exact keywords present in the query (e.g., "eyes", "survive", "truly") and maps them to the corresponding text spans reliably. Because the passage is lexically consistent — the same words used in the query appear in the relevant chunks — graph-based scoring assigns high scores to the correct chunks.

**Vector retrieval** underperformed relative to graph on this dataset. Short queries against short chunks produce embedding vectors that are semantically close but not always well-separated, particularly when multiple chunks share the same topic domain. The result is that the first relevant chunk is often retrieved, but the second relevant chunk is displaced by a semantically adjacent but incorrect chunk.

**Hybrid retrieval** closely matched graph retrieval on all three queries. When graph precision is already high, the fusion step does not reorder results significantly; the vector signal adds little additional information over what graph already ranks correctly. This is a known property of linear score fusion: the stronger component dominates when its scores are consistently high.

---

## Key Findings

1. **Graph retrieval reduces false negatives on lexically consistent text.**  
Graph retrieval reduces false negatives by leveraging explicit lexical matching,
which is particularly effective in low-resource settings where semantic embeddings
are insufficiently discriminative.

2. **Hybrid ≈ Graph in this benchmark.**  
Hybrid retrieval results are nearly identical to Graph retrieval.
This indicates that graph-based signals dominate the fusion stage,
while vector similarity contributes limited additional ranking signal.

This suggests that the current fusion strategy may be under-utilizing vector signals,
and could benefit from calibrated weighting or normalization.

3. **Vector retrieval is more prone to rank displacement errors.**  
Vector retrieval often retrieves one relevant chunk but fails to include all relevant chunks within top-K,
due to semantic similarity overlap among chunks.

4. **Graph retrieval introduces additional false positives.**  
Graph expansion increases recall but may retrieve loosely related chunks,
especially when high-frequency terms are over-connected.

This reflects a classic recall–precision trade-off:
graph expansion improves coverage but introduces additional noise.

5. **Case-level diagnostics provide actionable insights.**  
Fields such as `relevant_ranks`, `false_negatives`, and `false_positives`
make it possible to identify retrieval failure modes directly,
which are not observable from aggregate metrics alone.

---

## Limitations

- **Dataset size**: Three queries over one document is insufficient to draw statistically robust conclusions. Results should be treated as qualitative diagnostics rather than benchmark benchmarks.
- **Annotation quality**: Ground-truth chunk IDs were assigned based on expected chunking behavior. If chunking boundaries shift (e.g., due to tokenization differences), the relevance labels may become misaligned.
- **Fixed retrieval depth**: All modes are evaluated at `k=3`. Performance comparisons may differ at other values of `k`, particularly for queries with more than two relevant chunks.
- **No LLM answer evaluation**: The analysis evaluates retrieval quality only. Whether the retrieved chunks actually produce a correct answer from the language model is not measured here.

---

## Next Steps

- **Expand the benchmark corpus.** Add more documents and queries to reduce sensitivity to individual chunking decisions and produce more reliable aggregate metrics.
- **Annotate chunk boundaries explicitly.** Rather than relying on predicted chunk IDs, store and compare chunk text content to decouple evaluation accuracy from chunker behavior.
- **Separate FP analysis by retrieval source.** Since `EvalResult.retrieved_chunk_ids` preserves order, it is possible to attribute each false positive to vector, graph, or fusion origin by cross-referencing `retrieval_debug`. This would identify whether FPs arise from the graph expansion step or the vector similarity step.
- **Track metric trends across development iterations.** Run `run_case_analysis.py` after each significant retrieval change and compare `relevant_ranks` distributions to detect regressions before they appear in aggregate summaries.

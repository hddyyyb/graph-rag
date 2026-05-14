# 50. Fusion Score Normalization

## 1. Background

The original fusion strategy directly summed:

final_score = alpha * vector_score + beta * graph_score

However, vector and graph scores were not on the same scale.

Example:

- vector_score ≈ 0.2 ~ 0.7
- graph_score ≈ 3 ~ 7

This caused graph-dominated fusion behavior.

---

## 2. Problem

### Observed Issues

- alpha / beta tuning had limited effect
- graph retrieval dominated final ranking
- hybrid retrieval behaved similarly to graph-only retrieval

### Root Cause

Raw scores from different retrieval systems were directly added without calibration.

---

## 3. Solution

A minimal min-max normalization strategy was introduced inside fusion logic.

Normalization is applied independently to:

- vector scores
- graph scores

Formula:

score_norm = (score - min) / (max - min)

Special case:

- if max == min:
  - positive scores → 1.0
  - zero scores → 0.0

---

## 4. Implementation Scope

Normalization is localized to:

QueryService._fuse_chunks()

No modifications were made to:

- VectorStore
- GraphStore
- retrieval algorithms
- chunking logic

---

## 5. Debug Improvements

Fusion debug output now includes:

- normalization_enabled
- normalization_method
- raw_vector_score
- raw_graph_score

This improves retrieval observability.

---

## 6. Validation

### Unit Tests

Added:

tests/application/test_fusion_normalization.py

Coverage includes:

- normalization correctness
- edge cases
- debug field validation
- alpha / beta ranking control

### Results

- normalized scores successfully constrained to [0, 1]
- alpha / beta can influence ranking under controlled samples
- score scale imbalance reduced

---

## 7. Current Limitations

On the current benchmark dataset:

- vector ranking and graph ranking are highly correlated
- some graph scores collapse into identical normalized values

Therefore, ranking changes remain limited on real samples.

---

## 8. Future Directions

Possible future improvements:

- TF-IDF / BM25-style weighting
- graph centrality penalty
- reranking
- learned fusion scoring
- multi-stage retrieval calibration
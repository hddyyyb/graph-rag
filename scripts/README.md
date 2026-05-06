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

## compare_vector_backends.py

Compare SQLite vs Qdrant vector store behavior.

- runs evaluation on the same dataset
- compares Recall@K / MRR
- measures latency

## inspect_qdrant_behavior.py

Inspect Qdrant retrieval behavior.

- observe top_k stability
- analyze score distribution
- test edge cases (unrelated queries)

## Notes

- scripts may use dedicated Qdrant collections (e.g. graphrag_eval)
- these collections are for testing only
- production collection should be managed separately
"""
Compare sqlite vs qdrant vector store backends on identical demo data.

Usage:
    python scripts/compare_vector_backends.py

Requirements:
    - qdrant: Qdrant server running at localhost:6333
    - sqlite: no external dependency (uses :memory:)

embedding_backend defaults to "hash" (deterministic, no model file needed).
Change BASE["embedding_backend"] to "sentence_transformer" for real embeddings.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_rag.api.main import build_settings, build_container
from graph_rag.evaluation.models import EvalSample
from graph_rag.evaluation.runner import evaluate_dataset

# Short texts: each < chunk_size (400) → produces exactly one chunk
# Chunk IDs will be "{doc_id}#0" (see FixedLengthChunker / RecursiveChunker)
DEMO_DOCS = [
    ("doc1", "Python is a popular programming language used for tutorials and learning."),
    ("doc2", "FastAPI is a modern web framework for building Python backend APIs quickly."),
    ("doc3", "Graph retrieval uses scoring functions to rank results from knowledge graphs."),
]

EVAL_SAMPLES = [
    EvalSample(query="python tutorial",          relevant_chunk_ids=["doc1#0"]),
    EvalSample(query="fastapi backend",           relevant_chunk_ids=["doc2#0"]),
    EvalSample(query="graph retrieval scoring",   relevant_chunk_ids=["doc3#0"]),
]

BASE = dict(
    graph_store_backend="memory",
    embedding_backend="sentence_transformer",
    llm_backend="fake",
    log_level="WARNING",
)

BACKENDS = [
    ("sqlite", dict(vector_store_backend="sqlite", sqlite_path=":memory:")),
    ("qdrant", dict(vector_store_backend="qdrant")),
]


def run_backend(name: str, extra: dict) -> None:
    settings = build_settings({**BASE, **extra})
    container = build_container(settings)
    ingest_svc = container["ingest_service"]
    query_svc  = container["query_service"]

    for doc_id, text in DEMO_DOCS:
        ingest_svc.ingest(doc_id=doc_id, text=text)

    t0 = time.perf_counter()
    _, summary = evaluate_dataset(
        samples=EVAL_SAMPLES,
        query_service=query_svc,
        mode="vector",
        k=3,
    )
    latency_ms = (time.perf_counter() - t0) * 1000

    print(
        f"backend={name:<8}  mode={summary.mode:<8}  "
        f"sample_count={summary.sample_count}  "
        f"avg_recall@{summary.k}={summary.avg_recall_at_k:.4f}  "
        f"avg_mrr={summary.avg_mrr:.4f}  "
        f"latency_ms={latency_ms:.1f}"
    )


if __name__ == "__main__":
    header = (
        f"{'backend':<10}  {'mode':<8}  "
        f"{'sample_count':<14}  avg_recall@k    avg_mrr   latency_ms"
    )
    print(header)
    print("-" * len(header))
    for name, extra in BACKENDS:
        run_backend(name, extra)

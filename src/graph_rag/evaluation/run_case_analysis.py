"""
Human-readable case-level error analysis script.

Run from the project root:
    python -m graph_rag.evaluation.run_case_analysis

Text and samples are copied from tests/evaluation/test_eval_real_benchmark.py
so this script stays self-contained without importing from test files.
"""
import sys
import os

# Ensure both src/ and the project root are on sys.path so that
# graph_rag.* and tests.* are importable when running this script directly.
_here = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_here, "..", "..", ".."))
_src_root = os.path.join(_project_root, "src")
for _p in (_src_root, _project_root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from graph_rag.evaluation.models import EvalSample
from graph_rag.evaluation.runner import evaluate_dataset
from graph_rag.infra.adapters import (
    SentenceTransformerEmbeddingProvider,
    InMemoryGraphStore,
    InMemoryVectorStore,
    RecursiveChunker,
)
from tests.helpers import build_test_ingest_service, build_basic_query_service


# ---------------------------------------------------------------------------
# Data — kept in sync with test_eval_real_benchmark.py
# ---------------------------------------------------------------------------

text = """At the far eastern corner of the Eastern Continent lies a region that appears on maps only as a boundary, without any label. People call it Meteor City.
    In the eyes of most, it is a barren wasteland, uninhabited and covered with centuries of accumulated garbage.
    Some information-privileged individuals know that people do live here, and in considerable numbers, surviving by scavenging waste.
    Those in high positions but operating in the shadows know even more — there are many people here, many exceptional individuals, who can be bought cheaply with food, drugs, or heavy metals.
    But only those who live in Meteor City truly understand it —
    This is Meteor City, a place that accepts all things discarded, where fallen stars gather."""

samples = [
    EvalSample(
        query="What is Meteor City like in the eyes of outsiders?",
        relevant_chunk_ids=["doc1#1", "doc1#2"],
    ),
    EvalSample(
        query="How do people in Meteor City primarily survive?",
        relevant_chunk_ids=["doc1#3", "doc1#4"],
    ),
    EvalSample(
        query="What is Meteor City truly like?",
        relevant_chunk_ids=["doc1#6", "doc1#7"],
    ),
]


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def _build_services():
    vector_store = InMemoryVectorStore()
    graph_store = InMemoryGraphStore()
    embedder = SentenceTransformerEmbeddingProvider()
    chunker = RecursiveChunker(chunk_size=100, chunk_overlap=0)

    ingest_service = build_test_ingest_service(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        chunker=chunker,
    )
    query_service = build_basic_query_service(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
    )
    return ingest_service, query_service


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def _print_mode_block(label: str, result):
    print(f"  [{label}]")
    print(f"    retrieved : {result.retrieved_chunk_ids}")
    print(f"    relevant  : {result.relevant_chunk_ids}")
    print(f"    ranks     : {result.relevant_ranks}")
    print(f"    FN        : {result.false_negatives}")
    print(f"    FP        : {result.false_positives}")
    print(f"    Recall@3  : {result.recall_at_k:.4f}")
    print(f"    MRR       : {result.mrr:.4f}")


def _print_results(vector_results, graph_results, hybrid_results):
    for i, sample in enumerate(samples):
        print()
        print(f"Query: {sample.query}")
        _print_mode_block("Vector", vector_results[i])
        _print_mode_block("Graph", graph_results[i])
        _print_mode_block("Hybrid", hybrid_results[i])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Building services and ingesting document...")
    ingest_service, query_service = _build_services()
    ingest_service.ingest(doc_id="doc1", text=text)
    print("Ingest complete.\n")

    K = 3

    vector_results, _ = evaluate_dataset(
        samples=samples, query_service=query_service, mode="vector", k=K
    )
    graph_results, _ = evaluate_dataset(
        samples=samples, query_service=query_service, mode="graph", k=K
    )
    hybrid_results, _ = evaluate_dataset(
        samples=samples, query_service=query_service, mode="hybrid", k=K
    )

    print("=" * 60)
    print("CASE-LEVEL ERROR ANALYSIS")
    print("=" * 60)
    _print_results(vector_results, graph_results, hybrid_results)
    print()


if __name__ == "__main__":
    main()

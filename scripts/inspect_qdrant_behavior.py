"""
Observe Qdrant vector retrieval behavior across queries, top_k values, and repeated runs.
Usage: python scripts/inspect_qdrant_behavior.py
Requires: Qdrant running at localhost:6333
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_rag.api.main import build_settings, build_container

DEMO_DOCS = [
    ("doc1", "Python is a popular programming language used for tutorials and learning."),
    ("doc2", "FastAPI is a modern web framework for building Python backend APIs quickly."),
    ("doc3", "Graph retrieval uses scoring functions to rank results from knowledge graphs."),
]

# chunk IDs are "{doc_id}#0" since each text is shorter than chunk_size (400)
TEXT_LOOKUP = {f"{doc_id}#0": text for doc_id, text in DEMO_DOCS}

QUERIES = [
    "python tutorial",
    "fastapi backend",
    "graph retrieval scoring",
    "completely unrelated cooking recipe",
]

TOP_K_VALUES = [1, 3, 5]
REPEAT = 3


def main():
    settings = build_settings(dict(
        vector_store_backend="qdrant",
        graph_store_backend="memory",
        embedding_backend="sentence_transformer",
        llm_backend="fake",
        log_level="WARNING",
    ))
    container = build_container(settings)
    ingest_svc = container["ingest_service"]
    query_svc  = container["query_service"]

    for doc_id, text in DEMO_DOCS:
        ingest_svc.ingest(doc_id=doc_id, text=text)
    print(f"Ingested {len(DEMO_DOCS)} docs.\n")

    for query in QUERIES:
        print("=" * 70)
        print(f"QUERY: {query!r}")

        for top_k in TOP_K_VALUES:
            print(f"\n  top_k={top_k}")

            for run in range(1, REPEAT + 1):
                result = query_svc.query(
                    query=query,
                    top_k=top_k,
                    enable_vector=True,
                    enable_graph=False,
                )
                citations = result.citations or []
                hits = [
                    f"{c['chunk_id']}  score={c['score']:.4f}  src={c['source']}"
                    f"  text={TEXT_LOOKUP.get(c['chunk_id'], '?')[:35]!r}"
                    for c in citations
                ]
                label = f"  run{run}: "
                if not hits:
                    print(label + "(empty)")
                else:
                    print(label + hits[0])
                    for h in hits[1:]:
                        print(" " * len(label) + h)


if __name__ == "__main__":
    main()

# 复用 src/graph_rag/evaluation/run_case_analysis.py

from graph_rag.evaluation.models import EvalSample
from graph_rag.evaluation.runner import evaluate_dataset
from graph_rag.infra.adapters import (
    SentenceTransformerEmbeddingProvider,
    InMemoryGraphStore,
    InMemoryVectorStore,
    RecursiveChunker,
)
from helpers import build_ingest_service, build_query_service



text = """At the far eastern corner of the Eastern Continent lies a region that appears on maps only as a boundary, without any label. People call it Meteor City.
    In the eyes of most, it is a barren wasteland, uninhabited and covered with centuries of accumulated garbage.
    Some information-privileged individuals know that people do live here, and in considerable numbers, surviving by scavenging waste.
    Those in high positions but operating in the shadows know even more — there are many people here, many exceptional individuals, who can be bought cheaply with food, drugs, or heavy metals.
    But only those who live in Meteor City truly understand it —
    This is Meteor City, a place that accepts all things discarded, where fallen stars gather."""

samples_chunk100 = [
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

samples = [
    EvalSample(
        query="What is Meteor City like in the eyes of outsiders?",
        relevant_chunk_ids=["doc1#1"],
    ),
    EvalSample(
        query="How do people in Meteor City primarily survive?",
        relevant_chunk_ids=["doc1#2"],
    ),
    EvalSample(
        query="What is Meteor City truly like?",
        relevant_chunk_ids=["doc1#4"],
    ),
]  # _chunk200


def _build_services():
    vector_store = InMemoryVectorStore()
    graph_store = InMemoryGraphStore()
    embedder = SentenceTransformerEmbeddingProvider()
    chunker = RecursiveChunker(chunk_size=200, chunk_overlap=0)

    ingest_service, vector_store = build_ingest_service(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        chunker=chunker,
    )
    
    query_service = build_query_service(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
    )
    return ingest_service, query_service, vector_store, graph_store, embedder, chunker


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


def _print_query_debug(query_service, sample, mode: str):
    answer = query_service.query(
        query=sample.query,
        top_k=3,
        enable_vector=(mode in ["vector", "hybrid"]),
        enable_graph=(mode in ["graph", "hybrid"]),
    )

    print(f"\n[DEBUG] {mode.upper()} | {sample.query}")
    print("citations:")
    for c in answer.citations:
        print(c)

    print("retrieval_debug:")
    print(answer.retrieval_debug)
    
    
    
def main():
    ingest_service, query_service, vector_store, graph_store, embedder, chunker = _build_services()
    ingest_service.ingest(doc_id="doc1", text=text)
    # vector_store._data (doc_id, chunk_id) -> (text, embedding)
    for id, chunk in vector_store._data.items():
        print("=" * 40)
        print(id)
        print(chunk[0])
    
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
    _print_results(vector_results, graph_results, hybrid_results)
    print()
    
    # 查看检索的具体结果：
    for sample in samples:
        _print_query_debug(query_service, sample, mode="hybrid")
        
    # 测 hybrid query mode 的 fusion_alpha fusion_beta
    weight_cases = [
        (0.2, 0.8),
        (0.5, 0.5),
        (0.8, 0.2),
    ]
    
    for alpha, beta in weight_cases:
        query_service = build_query_service(
            vector_store=vector_store,
            graph_store=graph_store,
            embedder=embedder,
            fusion_alpha=alpha,
            fusion_beta=beta,
        )
        hybrid_results, _ = evaluate_dataset(
            samples=samples, query_service=query_service, mode="hybrid", k=K
        )
        print("=" * 60)
        for i, sample in enumerate(samples):
            print()
            print(f"alpha={alpha}, beta={beta}")
            print(f"Query: {sample.query}")
            _print_mode_block("Hybrid", hybrid_results[i])
            
    


if __name__ == "__main__":
    main()

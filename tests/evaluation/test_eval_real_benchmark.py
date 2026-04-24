# Small real benchmark for offline retrieval evaluation on English text.
# Used to validate vector / graph / hybrid behavior under stable term extraction.

# 第1块：先写导入
import pytest
import os

from graph_rag.evaluation.models import EvalSample
from graph_rag.infra.adapters import (
    SentenceTransformerEmbeddingProvider,
    InMemoryGraphStore,
    InMemoryVectorStore,
    RecursiveChunker,
)
# evaluation入口
from graph_rag.evaluation.runner import evaluate_dataset

# 测试service构造方法
from tests.helpers import build_basic_query_service, build_test_ingest_service

# 第2块：先写测试数据
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

from neo4j import GraphDatabase
from graph_rag.infra.config import Settings
settings = Settings()
driver = GraphDatabase.driver(
    settings.neo4j_uri,
    auth=(settings.neo4j_username, settings.neo4j_password),
)

def test_real_benchmark_small_dataset():
    # 1. 构造测试用service
    vector_store = InMemoryVectorStore()
    graph_store = InMemoryGraphStore()
    embedder = SentenceTransformerEmbeddingProvider()
    chunker = RecursiveChunker(chunk_size=100, chunk_overlap=0)
    ingest_service = build_test_ingest_service(
        vector_store = vector_store, 
        graph_store = graph_store, 
        embedder = embedder, 
        chunker = chunker)
    query_service = build_basic_query_service(
        vector_store = vector_store, 
        graph_store = graph_store, 
        embedder = embedder, 
        )
    

    # 2. ingest这段真实文本
    ingest_result = ingest_service.ingest(
        doc_id="doc1",
        text=text,
    )

    
    print("ingest_result:", ingest_result)
    query_result = query_service.query(query="What is Meteor City like in the eyes of outsiders?")
    chunk_ids = [x["chunk_id"] for x in query_result.citations]
    print("retrieved_chunk_ids:", chunk_ids)

    
    query = "What is Meteor City like in the eyes of outsiders?"
    results = graph_store.search(query, top_k=3)

    

    # 3. 分别运行vector / graph / hybrid评估
    vector_results, vector_summary = evaluate_dataset(
        samples=samples,
        query_service=query_service,
        mode="vector",
        k=3,
    )
    graph_results, graph_summary = evaluate_dataset(
        samples=samples,
        query_service=query_service,
        mode="graph",
        k=3,
    )
    hybrid_results, hybrid_summary = evaluate_dataset(
        samples=samples,
        query_service=query_service,
        mode="hybrid",
        k=3,
    )
    # 4. 打印summary结果
    print("=== VECTOR ===")
    print(f"sample_count: {vector_summary.sample_count}")
    print(f"avg_recall_at_k: {vector_summary.avg_recall_at_k}")
    print(f"avg_mrr: {vector_summary.avg_mrr}")
    print("=== GRAPH ===")
    print(f"sample_count: {graph_summary.sample_count}")
    print(f"avg_recall_at_k: {graph_summary.avg_recall_at_k}")
    print(f"avg_mrr: {graph_summary.avg_mrr}")
    print("=== HYBRID ===")
    print(f"sample_count: {hybrid_summary.sample_count}")    
    print(f"avg_recall_at_k: {hybrid_summary.avg_recall_at_k}")
    print(f"avg_mrr: {hybrid_summary.avg_mrr}")


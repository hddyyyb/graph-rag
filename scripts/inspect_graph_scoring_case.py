"""
临时分析脚本：观察 GraphStore.search() 的打分细节。

运行方式：
  python scripts/inspect_graph_scoring_case.py [--backend in_memory|neo4j|both]

Neo4j 需要环境变量：NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD
可选：NEO4J_DATABASE
"""
import argparse
import os
import sys
import json

# 把 scripts/ 目录加进 path，以便复用 helpers.py
sys.path.insert(0, os.path.dirname(__file__))

from helpers import build_ingest_service, build_query_service
from graph_rag.infra.adapters import (
    SentenceTransformerEmbeddingProvider,
    InMemoryGraphStore,
    InMemoryVectorStore,
    RecursiveChunker,
)

# ---------------------------------------------------------------------------
# 测试语料与 queries（与 analyze_fusion_behavior.py 保持一致）
# ---------------------------------------------------------------------------
TEXT = """At the far eastern corner of the Eastern Continent lies a region that appears on maps only as a boundary, without any label. People call it Meteor City.
In the eyes of most, it is a barren wasteland, uninhabited and covered with centuries of accumulated garbage.
Some information-privileged individuals know that people do live here, and in considerable numbers, surviving by scavenging waste.
Those in high positions but operating in the shadows know even more — there are many people here, many exceptional individuals, who can be bought cheaply with food, drugs, or heavy metals.
But only those who live in Meteor City truly understand it —
This is Meteor City, a place that accepts all things discarded, where fallen stars gather."""

QUERIES = [
    "What is Meteor City like in the eyes of outsiders?",
    "How do people in Meteor City primarily survive?",
    "What is Meteor City truly like?",
]


# ---------------------------------------------------------------------------
# 打印辅助
# ---------------------------------------------------------------------------
SEP = "=" * 70
SEP2 = "-" * 50


def _print_debug(debug: dict) -> None:
    print(f"  query           : {debug.get('query')}")
    print(f"  direct_terms    : {debug.get('direct_terms')}")

    exp_terms = debug.get("expanded_terms", [])
    if exp_terms:
        print(f"  expanded_terms  : ({len(exp_terms)} items)")
        for et in exp_terms[:10]:
            print(f"    {et.get('query_term')} -> {et.get('expanded_term')}  weight={et.get('weight')}")
        if len(exp_terms) > 10:
            print(f"    ... (+{len(exp_terms) - 10} more)")
    else:
        print("  expanded_terms  : (none)")

    print(f"  weights         : {debug.get('weights')}")
    print(f"  scoring_formula : {debug.get('scoring_formula')}")
    print(f"  meta            : {debug.get('meta')}")

    chunks = debug.get("chunks", [])
    if not chunks:
        print("  chunks          : (no results)")
        return

    print(f"\n  --- chunks (sorted by score desc, {len(chunks)} total) ---")
    ranked = sorted(chunks, key=lambda c: -c.get("score", 0.0))
    for rank, chunk in enumerate(ranked, start=1):
        direct_score = chunk.get("direct_score", 0.0)
        expanded_score = chunk.get("expanded_score", 0.0)
        total = chunk.get("score", 0.0)
        dominant = "EXPANDED" if expanded_score > direct_score else "DIRECT"
        print(
            f"  #{rank:02d}  chunk_id={chunk.get('chunk_id')}  doc_id={chunk.get('doc_id')}"
        )
        print(
            f"       direct_hits={chunk.get('direct_hit_count')}  "
            f"expanded_hits={chunk.get('expanded_hit_count')}  "
            f"direct_score={direct_score:.4f}  "
            f"expanded_score={expanded_score:.4f}  "
            f"score={total:.4f}  "
            f"[dominant={dominant}]"
        )
        # top-5 expanded_hits
        hits = chunk.get("expanded_hits", [])
        if hits:
            top_hits = sorted(hits, key=lambda h: -h.get("contribution", 0.0))[:5]
            for h in top_hits:
                print(
                    f"         expanded_hit: {h.get('query_term')} -> {h.get('expanded_term')}  "
                    f"weight={h.get('weight')}  contribution={h.get('contribution'):.4f}"
                )


# ---------------------------------------------------------------------------
# 核心：执行一组 queries 并打印 debug
# ---------------------------------------------------------------------------
def _run_queries(graph_store, label: str) -> None:
    print(SEP)
    print(f"BACKEND: {label}")
    print(SEP)

    vector_store = InMemoryVectorStore()
    embedder = SentenceTransformerEmbeddingProvider()
    chunker = RecursiveChunker(chunk_size=200, chunk_overlap=0)

    ingest_service, vector_store = build_ingest_service(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        chunker=chunker,
    )
    ingest_service.ingest(doc_id="doc1", text=TEXT)

    query_service = build_query_service(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
    )

    for query in QUERIES:
        print()
        print(SEP2)
        print(f"QUERY: {query}")
        print(SEP2)

        answer = query_service.query(
            query=query,
            top_k=5,
            enable_vector=False,
            enable_graph=True,
        )

        debug = answer.retrieval_debug

        print("=== Retrieval Debug Summary ===")
        print(json.dumps(debug.get("summary", {}), ensure_ascii=False, indent=2))
        
        print("=== Ranking Preview ===")
        print(json.dumps(debug.get("ranking_preview", []), ensure_ascii=False, indent=2)) 
        
        print("=== Scoring Overview ===")
        print(json.dumps(debug.get("scoring_overview", {}), ensure_ascii=False, indent=2))

        print("=== Final Results ===")
        print(json.dumps(debug.get("final", {}), ensure_ascii=False, indent=2))  
        
        print("=== Graph Debug ===")
        _print_debug(debug.get("graph", {}))


# ---------------------------------------------------------------------------
# Neo4j helpers
# ---------------------------------------------------------------------------
def _build_neo4j_store():
    try:
        from neo4j import GraphDatabase
        from graph_rag.infra.config import Settings
        from graph_rag.api.main import build_graph_store
    except ImportError as e:
        print(f"[ERROR] Cannot import required modules: {e}")
        return None

    # 与 main.py 保持一致：通过 Settings 加载配置（读 .env + 默认值）
    try:
        settings = Settings(graph_store_backend="neo4j")
    except Exception as e:
        print(f"[SKIP] Neo4j backend: Settings validation failed — {e}")
        return None

    print(
        f"[INFO] Neo4j: uri={settings.neo4j_uri}  "
        f"user={settings.neo4j_username}  db={settings.neo4j_database}"
    )

    # 连通性检查
    try:
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
        driver.verify_connectivity()
    except Exception as e:
        print(f"[SKIP] Neo4j backend: cannot connect — {e}")
        driver.close()
        return None

    store = build_graph_store(settings)

    # 清空已有数据，避免上次运行残留干扰
    try:
        with driver.session(database=settings.neo4j_database) as session:
            session.run("MATCH (n) DETACH DELETE n")
    except Exception:
        pass

    return store


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Inspect graph scoring debug info")
    parser.add_argument(
        "--backend",
        choices=["in_memory", "neo4j", "both"],
        default="both",
        help="Which graph backend to use (default: in_memory)",
    )
    args = parser.parse_args()

    run_memory = args.backend in ("in_memory", "both")
    run_neo4j = args.backend in ("neo4j", "both")

    if run_memory:
        _run_queries(InMemoryGraphStore(), label="InMemoryGraphStore")

    if run_neo4j:
        neo4j_store = _build_neo4j_store()
        if neo4j_store is not None:
            _run_queries(neo4j_store, label="Neo4jGraphStore")


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
import uuid
from dotenv import load_dotenv

load_dotenv()

import pytest
from neo4j import GraphDatabase

from graph_rag.domain.graph_models import ChunkGraphRecord
from graph_rag.infra.adapters import Neo4jGraphStore

"""
Integration tests for Neo4jGraphStore.

These tests validate the infrastructure adapter itself rather than only
the API-level closed loop. Coverage includes:

- single-record and batch upsert
- term-based retrieval
- top_k truncation
- ranking by term overlap
- boundary cases such as empty queries and invalid top_k
- persistence of core graph relations:
  Chunk-[:MENTIONS]->Term
  Term-[:CO_OCCURS_WITH]->Term

Overall, this test module focuses on real integration between:
Python code + Neo4j driver + a real Neo4j database.
"""


# -----------------------------------------------------------------------------
# test config helpers
# -----------------------------------------------------------------------------


def _random_suffix() -> str:
    """Generate a short random suffix to avoid ID collisions across tests."""
    return uuid.uuid4().hex[:8]




# -----------------------------------------------------------------------------
# test helpers
# -----------------------------------------------------------------------------

def _make_store(neo4j_driver, neo4j_database) -> Neo4jGraphStore:
    """
    Create the system under test.

    This helper keeps store construction consistent across test cases.
    """
    return Neo4jGraphStore(
        driver=neo4j_driver,
        database=neo4j_database,
        ensure_schema_on_init=True,
    )


def _make_record(
    *,
    chunk_id: str,
    doc_id: str,
    text: str,
    terms: list[str] | None = None,
):
    """
    Build a ChunkGraphRecord for tests.

    Adjust this helper if ChunkGraphRecord uses a different constructor.

    Current assumption:
    ChunkGraphRecord(chunk_id=..., doc_id=..., text=..., terms=...)
    If your model does not support 'terms', remove that field here.
    """
    if terms is None:
        return ChunkGraphRecord(
            chunk_id=chunk_id,
            doc_id=doc_id,
            text=text,
        )

    return ChunkGraphRecord(
        chunk_id=chunk_id,
        doc_id=doc_id,
        text=text,
        terms=terms,
    )


# -----------------------------------------------------------------------------
# tests
# -----------------------------------------------------------------------------

@pytest.mark.integration
def test_upsert_and_search_basic(neo4j_driver, neo4j_database, clean_graph):
    """
    Verify that a single upserted graph record can be retrieved by search().
    """
    store = _make_store(neo4j_driver, neo4j_database)

    chunk_id = f"c1_{_random_suffix()}"
    doc_id = f"d1_{_random_suffix()}"

    store.upsert_chunk_graphs(
        [
            _make_record(
                chunk_id=chunk_id,
                doc_id=doc_id,
                text="Neo4j graph retrieval supports relationship queries",
            )
        ]
    )

    results = store.search("relationship", top_k=3)

    assert len(results) == 1
    assert results[0].chunk_id == chunk_id
    assert results[0].doc_id == doc_id
    assert "Neo4j graph retrieval supports relationship queries" == results[0].text
    assert results[0].source == "graph"
    assert results[0].score >= 1.0    # score 的计算：WITH c, count(DISTINCT t) AS score


@pytest.mark.integration
def test_search_returns_empty_for_unknown_term(neo4j_driver, neo4j_database, clean_graph):
    """
    Verify that search() returns an empty list when the query term does not exist.
    """
    store = _make_store(neo4j_driver, neo4j_database)

    store.upsert_chunk_graphs(
        [
            _make_record(
                chunk_id=f"c1_{_random_suffix()}",
                doc_id=f"d1_{_random_suffix()}",
                text="vector retrieval and graph retrieval are both supported",
            )
        ]
    )

    results = store.search("nonexistentterm", top_k=3)

    assert results == []


@pytest.mark.integration
def test_search_respects_top_k(neo4j_driver, neo4j_database, clean_graph):
    """
    Verify that search() respects the requested top_k limit.
    """
    store = _make_store(neo4j_driver, neo4j_database)

    records = [
        _make_record(
            chunk_id=f"c1_{_random_suffix()}",
            doc_id="doc_a",
            text="graph retrieval uses term matching",
        ),
        _make_record(
            chunk_id=f"c2_{_random_suffix()}",
            doc_id="doc_b",
            text="graph databases support graph retrieval",
        ),
        _make_record(
            chunk_id=f"c3_{_random_suffix()}",
            doc_id="doc_c",
            text="retrieval pipelines may combine vector and graph logic",
        ),
    ]
    store.upsert_chunk_graphs(records)

    results = store.search("graph retrieval", top_k=2)

    assert len(results) == 2
    assert all(item.source == "graph" for item in results)


@pytest.mark.integration
def test_search_returns_multiple_hits_sorted_by_term_overlap(
    neo4j_driver,
    neo4j_database,
    clean_graph,
):
    """
    Verify that multiple hits are sorted by descending term overlap score.
    """
    store = _make_store(neo4j_driver, neo4j_database)

    high_match_chunk_id = f"c_high_{_random_suffix()}"
    low_match_chunk_id = f"c_low_{_random_suffix()}"

    store.upsert_chunk_graphs(
        [
            _make_record(
                chunk_id=high_match_chunk_id,
                doc_id="doc_1",
                text="graph retrieval uses term matching for chunk ranking",
            ),
            _make_record(
                chunk_id=low_match_chunk_id,
                doc_id="doc_2",
                text="graph systems are useful",
            ),
        ]
    )

    results = store.search("graph retrieval term", top_k=5)

    assert len(results) == 2
    assert results[0].chunk_id == high_match_chunk_id
    assert results[0].score >= results[1].score


@pytest.mark.integration
def test_search_returns_empty_for_empty_query(neo4j_driver, neo4j_database, clean_graph):
    """
    Verify that empty or whitespace-only queries return no results.
    """
    store = _make_store(neo4j_driver, neo4j_database)

    store.upsert_chunk_graphs(
        [
            _make_record(
                chunk_id=f"c1_{_random_suffix()}",
                doc_id="doc_1",
                text="some graph text here",
            )
        ]
    )

    assert store.search("", top_k=3) == []
    assert store.search("   ", top_k=3) == []


@pytest.mark.integration
def test_search_returns_empty_when_top_k_is_non_positive(
    neo4j_driver,
    neo4j_database,
    clean_graph,
):
    """
    Verify that non-positive top_k values return no results.
    """
    store = _make_store(neo4j_driver, neo4j_database)

    store.upsert_chunk_graphs(
        [
            _make_record(
                chunk_id=f"c1_{_random_suffix()}",
                doc_id="doc_1",
                text="graph retrieval text",
            )
        ]
    )

    assert store.search("graph", top_k=0) == []
    assert store.search("graph", top_k=-1) == []


@pytest.mark.integration
def test_upsert_supports_multiple_records(neo4j_driver, neo4j_database, clean_graph):
    """
    Verify that batch upsert persists multiple records correctly.
    """
    store = _make_store(neo4j_driver, neo4j_database)

    chunk_id_1 = f"c1_{_random_suffix()}"
    chunk_id_2 = f"c2_{_random_suffix()}"

    store.upsert_chunk_graphs(
        [
            _make_record(
                chunk_id=chunk_id_1,
                doc_id="doc_1",
                text="neo4j stores graph nodes and relationships",
            ),
            _make_record(
                chunk_id=chunk_id_2,
                doc_id="doc_2",
                text="query services can consume graph retrieval results",
            ),
        ]
    )

    results_1 = store.search("relationships", top_k=5)
    results_2 = store.search("services", top_k=5)

    assert any(item.chunk_id == chunk_id_1 for item in results_1)
    assert any(item.chunk_id == chunk_id_2 for item in results_2)


@pytest.mark.integration
def test_upsert_uses_record_terms_if_available(neo4j_driver, neo4j_database, clean_graph):
    """
    Verify that explicit record terms are used when provided, even if the
    corresponding keyword does not appear in the raw text.
    """
    store = _make_store(neo4j_driver, neo4j_database)

    chunk_id = f"c_terms_{_random_suffix()}"

    store.upsert_chunk_graphs(
        [
            _make_record(
                chunk_id=chunk_id,
                doc_id="doc_terms",
                text="this text intentionally does not contain the keyword",
                terms=["neo4j", "cypher", "graph"],
            )
        ]
    )

    results = store.search("cypher", top_k=3)

    assert len(results) == 1
    assert results[0].chunk_id == chunk_id


@pytest.mark.integration
def test_co_occurs_edges_are_created(neo4j_driver, neo4j_database, clean_graph):
    """
    Verify that CO_OCCURS_WITH edges are persisted when multiple terms belong
    to the same record.

    This checks storage-side behavior directly in Neo4j. The relation is not
    necessarily used by search() yet, but it is still part of the intended schema.
    """
    store = _make_store(neo4j_driver, neo4j_database)

    store.upsert_chunk_graphs(
        [
            _make_record(
                chunk_id=f"c1_{_random_suffix()}",
                doc_id="doc_1",
                text="",
                terms=["neo4j", "graph", "retrieval"],
            )
        ]
    )

    with neo4j_driver.session(database=neo4j_database) as session:
        result = session.run(
            """
            MATCH (:Term {name: "graph"})-[r:CO_OCCURS_WITH]-(:Term {name: "neo4j"})
            RETURN count(r) AS cnt
            """
        )
        row = result.single()

    assert row is not None
    assert row["cnt"] >= 1


@pytest.mark.integration
def test_mentions_edges_are_created(neo4j_driver, neo4j_database, clean_graph):
    """
    Verify that Chunk -> Term MENTIONS edges are persisted correctly.
    """
    store = _make_store(neo4j_driver, neo4j_database)

    chunk_id = f"c_mentions_{_random_suffix()}"

    store.upsert_chunk_graphs(
        [
            _make_record(
                chunk_id=chunk_id,
                doc_id="doc_mentions",
                text="graph retrieval pipeline",
            )
        ]
    )

    with neo4j_driver.session(database=neo4j_database) as session:
        result = session.run(
            """
            MATCH (c:Chunk {chunk_id: $chunk_id})-[:MENTIONS]->(t:Term {name: "graph"})
            RETURN count(t) AS cnt
            """,
            chunk_id=chunk_id,
        )
        row = result.single()

    assert row is not None
    assert row["cnt"] == 1



@pytest.mark.integration
def test_neo4j_graph_store_expanded_terms_sorted_by_weight(neo4j_driver, neo4j_config):
    store = Neo4jGraphStore(
        driver=neo4j_driver,
        database=neo4j_config["neo4j_database"],
        expand_per_term_limit=5,
        direct_hit_weight=1.0,
        expanded_hit_weight=0.5,
        max_expanded_terms=10,
    )

    store.upsert_chunk_graphs(
        [
            ChunkGraphRecord(doc_id="d1", chunk_id="c1", text="rag graph", terms=["rag", "graph"]),
            ChunkGraphRecord(doc_id="d2", chunk_id="c2", text="rag graph", terms=["rag", "graph"]),
            ChunkGraphRecord(doc_id="d3", chunk_id="c3", text="rag graph", terms=["rag", "graph"]),
            ChunkGraphRecord(doc_id="d4", chunk_id="c4", text="rag ranking", terms=["rag", "ranking"]),
        ]
    )

    store.search("rag", top_k=10)
    debug = store.get_last_debug()

    assert debug is not None
    assert debug["expanded_terms"][0]["expanded_term"] == "graph"
    assert debug["expanded_terms"][0]["weight"] > debug["expanded_terms"][1]["weight"]
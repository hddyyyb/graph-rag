from __future__ import annotations
from typing import Generator
import os
from neo4j import GraphDatabase
import pytest

from dotenv import load_dotenv

load_dotenv()
# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from graph_rag.api.main import create_app


# -----------------------------------------------------------------------------
# environment helpers
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# fixtures
# -----------------------------------------------------------------------------
import pytest

from graph_rag.infra.adapters import InMemoryGraphStore, Neo4jGraphStore


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def memory_store():
    return InMemoryGraphStore(
        expand_per_term_limit=2,
        direct_hit_weight=1.0,
        expanded_hit_weight=0.5,
    )


@pytest.fixture
def neo4j_store(neo4j_driver, neo4j_config, clean_graph):
    return Neo4jGraphStore(
        driver=neo4j_driver,
        database=neo4j_config["neo4j_database"],
        expand_per_term_limit=2,
        direct_hit_weight=1.0,
        expanded_hit_weight=0.5,
    )



@pytest.fixture
def neo4j_driver():
    """
    Provide a real Neo4j driver for integration tests.

    The driver is created before the test and automatically closed after it.
    """
    uri, username, password, _ = _require_neo4j_env()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    try:
        yield driver
    finally:
        driver.close()


@pytest.fixture
def neo4j_database() -> str | None:
    """Return the configured Neo4j database name, if provided."""
    _, _, _, database = _require_neo4j_env()
    return database


@pytest.fixture
def clean_graph(neo4j_driver, neo4j_database):
    """
    Best-effort cleanup before and after each test.

    For local isolated testing, clearing the whole graph is acceptable.
    If safer multi-tenant testing is needed later, this can be replaced
    with prefix-based cleanup.
    """
    _wipe_all_nodes(neo4j_driver, neo4j_database)
    try:
        yield
    finally:
        _wipe_all_nodes(neo4j_driver, neo4j_database)


# -----------------------------------------------------------------------------
# cleanup utilities
# -----------------------------------------------------------------------------

def _wipe_all_nodes(driver, database: str | None) -> None:
    """Remove all nodes and relationships from the test database."""
    with driver.session(database=database) as session:
        session.run("MATCH (n) DETACH DELETE n")

        

def _require_neo4j_env() -> tuple[str, str, str, str | None]:
    """
    Read Neo4j connection info from environment variables.

    Required:
    - NEO4J_URI
    - NEO4J_USERNAME
    - NEO4J_PASSWORD

    Optional:
    - NEO4J_DATABASE

    If required variables are missing, the tests will be skipped.
    """
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE")

    if not uri or not username or not password:
        pytest.skip(
            "Neo4j test env is not configured. "
            "Please set NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD."
        )

    return uri, username, password, database


# -----------------------------------------------------------------------------
# fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def neo4j_config(): 
    """
    Provide Neo4j connection settings as a dictionary.
    """
    uri, username, password, database = _require_neo4j_env()
    return {
        "neo4j_uri": uri,
        "neo4j_username": username,
        "neo4j_password": password,
        "neo4j_database": database,
    }


@pytest.fixture
def neo4j_driver(neo4j_config):
    """
    Provide a real Neo4j driver instance.

    The driver is automatically closed after the test.
    """
    driver = GraphDatabase.driver(
        neo4j_config["neo4j_uri"],
        auth=(neo4j_config["neo4j_username"], neo4j_config["neo4j_password"]),
    )
    try:
        yield driver  
    finally:
        driver.close()
    # yield = “返回一个值，但函数不会结束，下次还能从这里继续执行”

#  pytest 在同一个 scope 生命周期内会缓存 fixture 的结果

# -----------------------------------------------------------------------------
# graph cleanup
# -----------------------------------------------------------------------------

def _wipe_all_nodes(driver, database: str | None) -> None:
    """
    Remove all nodes and relationships from the test database.

    This ensures test isolation across runs.
    """
    with driver.session(database=database) as session:  # ① 打开一个 session:“我现在要操作 Neo4j 这个数据库了”
        session.run("MATCH (n) DETACH DELETE n")  # ② 执行 Cypher
        # MATCH (n) 找到所有节点
        # DETACH DELETE n 删除这些节点和它们的关系


@pytest.fixture
def clean_graph(neo4j_driver, neo4j_config):  # 得到yield driver, 和neo4j_config返回值
    _wipe_all_nodes(neo4j_driver, neo4j_config["neo4j_database"])  # Step 1：测试开始前
    try:
        yield    # Step 2：进入测试
    finally:    # Step 4：测试结束后
        _wipe_all_nodes(neo4j_driver, neo4j_config["neo4j_database"])


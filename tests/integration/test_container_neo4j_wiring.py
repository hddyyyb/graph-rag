from graph_rag.api.main import build_container, create_app
from graph_rag.infra.config.settings import Settings
import pytest
import os


@pytest.mark.integration
def test_build_container_uses_neo4j_graph_store(neo4j_config):
    settings = Settings(
        vector_store_backend="memory",
        graph_store_backend="neo4j",
        neo4j_uri=neo4j_config["neo4j_uri"],
        neo4j_username=neo4j_config["neo4j_username"],
        neo4j_password=neo4j_config["neo4j_password"],
        neo4j_database=neo4j_config["neo4j_database"],
        llm_backend="fake",
    )

    container = build_container(settings)
    assert container["graph_store"].__class__.__name__ == "Neo4jGraphStore"


@pytest.mark.integration
def test_create_app_uses_neo4j_graph_store(neo4j_config):
    app = create_app(
        settings_override={
            "vector_store_backend": "memory",
            "graph_store_backend": "neo4j",
            "neo4j_uri": neo4j_config["neo4j_uri"],
            "neo4j_username": neo4j_config["neo4j_username"],
            "neo4j_password": neo4j_config["neo4j_password"],
            "neo4j_database": neo4j_config["neo4j_database"],
        }
    )
    assert app.state.container["graph_store"].__class__.__name__ == "Neo4jGraphStore"
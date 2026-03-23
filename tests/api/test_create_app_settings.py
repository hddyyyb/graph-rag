from __future__ import annotations

from graph_rag.api.main import create_app


# 测试1：override 能进 Settings
def test_create_app_applies_settings_override(tmp_path):
    app = create_app(
        settings_override={
            "vector_store_backend": "sqlite",
            "sqlite_path": str(tmp_path / "test.db"),
            "graph_store_backend": "memory",
        }
    )

    settings = app.state.settings
    assert settings.vector_store_backend == "sqlite"
    assert settings.graph_store_backend == "memory"
    assert settings.sqlite_path.endswith("test.db")


# 测试2：container 用的是同一个 settings
def test_create_app_container_receives_final_settings(tmp_path):
    app = create_app(
        settings_override={
            "vector_store_backend": "sqlite",
            "sqlite_path": str(tmp_path / "test.db"),
        }
    )

    assert app.state.container["settings"] is app.state.settings


# 测试3：override 后 wiring 正确
def test_create_app_override_selects_sqlite_vector_store(tmp_path):
    app = create_app(
        settings_override={
            "vector_store_backend": "sqlite",
            "sqlite_path": str(tmp_path / "test.db"),
            "graph_store_backend": "memory",
        }
    )

    vector_store = app.state.container["vector_store"]
    assert vector_store.__class__.__name__ == "SQLiteVectorStore"
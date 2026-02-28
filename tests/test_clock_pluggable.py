from __future__ import annotations

from graph_rag.api.main import create_app

from fastapi.testclient import TestClient
from graph_rag.infra.adapters import FixedClock
from graph_rag.infra.observability.logging import SimpleTrace

def test_clock_pluggable():
    app = create_app()

    client = TestClient(app)

    app.state.container['clock'] = FixedClock("2000-01-01T00:00:00Z")

    app.state.container["trace"] = SimpleTrace(clock=app.state.container["clock"])


    r = client.get("/health")
    assert r.status_code == 200


    assert app.state.container["trace"].started_at == "2000-01-01T00:00:00Z"
from graph_rag.evaluation.models import EvalSample
from graph_rag.evaluation.runner import evaluate_sample


class FakeQueryResult:
    def __init__(self, citations):
        self.citations = citations


class FakeQueryService:
    def __init__(self):
        self.last_kwargs: dict[str, object] = {}

    def query(self, **kwargs):
        self.last_kwargs = kwargs
        return FakeQueryResult(
            citations=[
                {"chunk_id": "c2"},
                {"chunk_id": "c3"},
                {"chunk_id": "c1"},
            ]
        )


def test_evaluate_sample_hybrid():
    sample = EvalSample(query="test query", relevant_chunk_ids=["c1"])
    service = FakeQueryService()

    result = evaluate_sample(sample, service, mode="hybrid", k=2)

    assert result.mode == "hybrid"
    assert result.retrieved_chunk_ids == ["c2", "c3", "c1"]
    assert result.recall_at_k == 0.0
    assert result.mrr == 1 / 3
    assert service.last_kwargs["enable_vector"] is True
    assert service.last_kwargs["enable_graph"] is True
    assert service.last_kwargs["top_k"] == 2


def test_evaluate_sample_vector_mode_flags():
    sample = EvalSample(query="test query", relevant_chunk_ids=["c1"])
    service = FakeQueryService()

    evaluate_sample(sample, service, mode="vector", k=3)

    assert service.last_kwargs["enable_vector"] is True
    assert service.last_kwargs["enable_graph"] is False


def test_evaluate_sample_graph_mode_flags():
    sample = EvalSample(query="test query", relevant_chunk_ids=["c1"])
    service = FakeQueryService()

    evaluate_sample(sample, service, mode="graph", k=3)

    assert service.last_kwargs["enable_vector"] is False
    assert service.last_kwargs["enable_graph"] is True


def test_evaluate_sample_invalid_mode_raises():
    sample = EvalSample(query="test query", relevant_chunk_ids=["c1"])
    service = FakeQueryService()

    import pytest
    with pytest.raises(ValueError):
        evaluate_sample(sample, service, mode="unknown", k=3)
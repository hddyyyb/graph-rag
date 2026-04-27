from graph_rag.evaluation.models import EvalSample
from graph_rag.evaluation.runner import evaluate_sample


class FakeResult:
    def __init__(self, chunk_ids: list[str]):
        self.citations = [{"chunk_id": cid} for cid in chunk_ids]


class FakeQueryService:
    def __init__(self, chunk_ids: list[str]):
        self._chunk_ids = chunk_ids

    def query(self, **kwargs):
        return FakeResult(self._chunk_ids)


def test_full_hit():
    service = FakeQueryService(chunk_ids=["c1", "c2", "c3"])
    sample = EvalSample(query="q", relevant_chunk_ids=["c1", "c2"])
    result = evaluate_sample(sample=sample, query_service=service, mode="hybrid", k=5)

    assert result.relevant_ranks == {"c1": 1, "c2": 2}
    assert result.false_negatives == []
    assert result.false_positives == ["c3"]


def test_partial_hit():
    service = FakeQueryService(chunk_ids=["c1", "c3"])
    sample = EvalSample(query="q", relevant_chunk_ids=["c1", "c2"])
    result = evaluate_sample(sample=sample, query_service=service, mode="hybrid", k=5)

    assert result.relevant_ranks == {"c1": 1, "c2": None}
    assert result.false_negatives == ["c2"]
    assert result.false_positives == ["c3"]


def test_full_miss():
    service = FakeQueryService(chunk_ids=["c3", "c4"])
    sample = EvalSample(query="q", relevant_chunk_ids=["c1", "c2"])
    result = evaluate_sample(sample=sample, query_service=service, mode="hybrid", k=5)

    assert result.relevant_ranks == {"c1": None, "c2": None}
    assert result.false_negatives == ["c1", "c2"]
    assert result.false_positives == ["c3", "c4"]


def test_empty_retrieved():
    service = FakeQueryService(chunk_ids=[])
    sample = EvalSample(query="q", relevant_chunk_ids=["c1"])
    result = evaluate_sample(sample=sample, query_service=service, mode="hybrid", k=5)

    assert result.relevant_ranks == {"c1": None}
    assert result.false_negatives == ["c1"]
    assert result.false_positives == []

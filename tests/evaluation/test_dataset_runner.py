import pytest

from graph_rag.evaluation.models import EvalSample
from graph_rag.evaluation.runner import evaluate_dataset


class FakeQueryResult:
    def __init__(self, citations):
        self.citations = citations


class FakeQueryService:
    def query(
        self,
        *,
        query: str,
        top_k=None,
        enable_vector=None,
        enable_graph=None,
        options=None,
        min_score=None,
    ):
        mapping = {
            "q1": [{"chunk_id": "c1"}, {"chunk_id": "c2"}],
            "q2": [{"chunk_id": "c3"}, {"chunk_id": "c4"}],
        }
        return FakeQueryResult(citations=mapping.get(query, []))


samples = [
    EvalSample(query="q1", relevant_chunk_ids=["c1"]),
    EvalSample(query="q2", relevant_chunk_ids=["c5"]),
]


def test_evaluate_dataset_success():
    service = FakeQueryService()

    results, summary = evaluate_dataset(
        samples=samples,
        query_service=service,
        mode="hybrid",
        k=2,
    )

    assert len(results) == 2

    assert summary.mode == "hybrid"
    assert summary.k == 2
    assert summary.sample_count == 2
    assert summary.avg_recall_at_k == 0.5
    assert summary.avg_mrr == 0.5


def test_evaluate_dataset_empty_samples_raises():
    service = FakeQueryService()

    with pytest.raises(ValueError):
        evaluate_dataset(
            samples=[],
            query_service=service,
            mode="hybrid",
            k=2,
        )
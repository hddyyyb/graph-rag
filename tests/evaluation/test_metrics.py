import pytest

from graph_rag.evaluation.metrics import recall_at_k, mrr


def test_recall_at_k_hit():
    retrieved = ["c1", "c2", "c3"]
    relevant = ["c2", "c4"]

    result = recall_at_k(retrieved, relevant, k=2)

    assert result == 0.5


def test_recall_at_k_multiple_hits():
    retrieved = ["c1", "c2", "c3"]
    relevant = ["c1", "c2", "c5"]

    result = recall_at_k(retrieved, relevant, k=2)

    assert result == 2 / 3


def test_recall_at_k_no_hit():
    retrieved = ["c1", "c2", "c3"]
    relevant = ["c4", "c5"]

    result = recall_at_k(retrieved, relevant, k=3)

    assert result == 0.0


def test_recall_at_k_empty_retrieved():
    retrieved = []
    relevant = ["c1", "c2"]

    result = recall_at_k(retrieved, relevant, k=3)

    assert result == 0.0


def test_recall_at_k_empty_relevant_raises():
    with pytest.raises(ValueError):
        recall_at_k(["c1"], [], k=1)


def test_mrr_first_hit():
    retrieved = ["c2", "c3", "c4"]
    relevant = ["c2"]

    result = mrr(retrieved, relevant)

    assert result == 1.0


def test_mrr_third_hit():
    retrieved = ["c1", "c2", "c3"]
    relevant = ["c3"]

    result = mrr(retrieved, relevant)

    assert result == 1 / 3


def test_mrr_no_hit():
    retrieved = ["c1", "c2", "c3"]
    relevant = ["c4"]

    result = mrr(retrieved, relevant)

    assert result == 0.0
    
def test_recall_at_k_invalid_k_raises():
    with pytest.raises(ValueError):
        recall_at_k(["c1"], ["c1"], k=0)


def test_mrr_empty_relevant_raises():
    with pytest.raises(ValueError):
        mrr(["c1"], [])
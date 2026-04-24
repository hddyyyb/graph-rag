from __future__ import annotations

from tests.helpers import build_test_service


def test_time_record():
    service = build_test_service()
    answer = service.query(query = "hello")

    assert answer.retrieval_debug["timings"]["embedding_time"] >= 0
    assert answer.retrieval_debug["timings"]["vector_retrieval_time"] >= 0
    assert answer.retrieval_debug["timings"]["graph_retrieval_time"] >= 0
    assert answer.retrieval_debug["timings"]["postprocess_time"] >= 0
    assert answer.retrieval_debug["timings"]["llm_generation_time"] >= 0


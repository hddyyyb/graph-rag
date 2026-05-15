"""
Day41: expansion_score_cap 最小测试

验证：
- expanded_score 超过 cap 时，score 使用 capped_expanded_score
- expanded_score 未超过 cap 时，score 不变
- cap=None 时保持旧行为
"""
import pytest
from graph_rag.domain.graph_models import ChunkGraphRecord
from graph_rag.infra.adapters.in_memory_graph_store import InMemoryGraphStore


def _build_store_with_records(expansion_score_cap):
    """
    构造一个共现图使 c1 的 expanded_score 可控：
    - c1: terms=[a, b, c]  -> a-b, a-c, b-c 各共现一次
    - c2: terms=[a, d]     -> a-d 共现一次
    查询 "x"，其中 x 与 a 共现（通过 c3 建立），则 c1/c2 都有 expanded hits。
    """
    store = InMemoryGraphStore(
        expand_per_term_limit=10,
        direct_hit_weight=1.0,
        expanded_hit_weight=1.0,   # contribution = edge_weight * 1.0，方便计算
        max_expanded_terms=20,
        expansion_score_cap=expansion_score_cap,
    )
    # c3 让 x 与 a/b/c 共现，形成扩展路径
    records = [
        ChunkGraphRecord(chunk_id="c1", doc_id="d1", text="", terms=["alpha", "beta", "gamma"]),
        ChunkGraphRecord(chunk_id="c2", doc_id="d1", text="", terms=["alpha", "delta"]),
        ChunkGraphRecord(chunk_id="c3", doc_id="d1", text="", terms=["queryterm", "alpha", "beta", "gamma"]),
    ]
    store.upsert_chunk_graphs(records)
    return store


def test_cap_applied_when_exceeded():
    # 1. 超过cap时是否截断

    """expanded_score > cap 时，score = direct_score + cap"""
    cap = 0.1
    store = _build_store_with_records(expansion_score_cap=cap)

    store.search("queryterm", top_k=10)
    debug = store.get_last_debug()
    assert debug is not None

    capped_chunks = [
        c for c in debug["chunks"]
        if c["expanded_score"] > cap
    ]

    assert capped_chunks, "至少应存在一个 expanded_score 超过 cap 的chunk"

    for c in capped_chunks:
        assert c["expansion_capped"] is True
        assert c["capped_expanded_score"] == pytest.approx(cap)
        assert c["score"] == pytest.approx(c["direct_score"] + cap)


def test_cap_not_applied_when_not_exceeded():
    # 2. 没超过cap时是否不变

    """expanded_score <= cap 时，score = direct_score + expanded_score（不截断）"""
    cap = 100.0  # 远大于任何可能的 expanded_score
    store = _build_store_with_records(expansion_score_cap=cap)

    results = store.search("queryterm", top_k=10)
    debug = store.get_last_debug()
    assert debug is not None

    chunk_map = {c["chunk_id"]: c for c in debug["chunks"]}

    for chunk_debug in chunk_map.values():
        assert chunk_debug["expansion_capped"] is False
        assert chunk_debug["capped_expanded_score"] == pytest.approx(
            chunk_debug["expanded_score"]
        )
        assert chunk_debug["score"] == pytest.approx(
            chunk_debug["direct_score"] + chunk_debug["expanded_score"]
        )


def test_cap_none_preserves_original_behavior():
    # 3. cap=None是否保持旧行为

    """cap=None 时行为与无 cap 完全一致"""
    store = _build_store_with_records(expansion_score_cap=None)

    results = store.search("queryterm", top_k=10)
    debug = store.get_last_debug()
    assert debug is not None

    chunk_map = {c["chunk_id"]: c for c in debug["chunks"]}

    for chunk_debug in chunk_map.values():
        assert chunk_debug["expansion_capped"] is False
        assert chunk_debug["expansion_score_cap"] is None
        assert chunk_debug["capped_expanded_score"] == pytest.approx(
            chunk_debug["expanded_score"]
        )
        assert chunk_debug["score"] == pytest.approx(
            chunk_debug["direct_score"] + chunk_debug["expanded_score"]
        )


def test_scoring_formula_reflects_cap():
    # 4. scoring_formula是否更新

    """scoring_formula 字符串在有 cap 时应包含 min(...)"""
    store_with_cap = InMemoryGraphStore(expansion_score_cap=2.0)
    store_no_cap = InMemoryGraphStore(expansion_score_cap=None)

    assert "min(" in store_with_cap._scoring_formula()
    assert "2.0" in store_with_cap._scoring_formula()
    assert "min(" not in store_no_cap._scoring_formula()


def test_weights_dict_contains_cap():
    # 5. debug['weights']是否暴露cap
    """debug['weights'] 中应暴露 expansion_score_cap"""
    store = InMemoryGraphStore(expansion_score_cap=3.5)
    store.upsert_chunk_graphs([
        ChunkGraphRecord(chunk_id="c1", doc_id="d1", text="hello world", terms=["hello", "world"]),
    ])
    store.search("hello", top_k=5)
    debug = store.get_last_debug()
    assert debug["weights"]["expansion_score_cap"] == pytest.approx(3.5)

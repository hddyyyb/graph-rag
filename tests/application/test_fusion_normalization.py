"""
Day40: Fusion Score Normalization 最小测试集
只测试 QueryService._normalize_scores 和 _fuse_chunks，不调用真实 embedding/store。
"""
import pytest
from graph_rag.application.query_service import QueryService
from graph_rag.domain.models import RetrievedChunk
from graph_rag.infra.adapters import FakeEmbeddingV2, FakeKernel, DefaultRetrievalPostProcessor
from graph_rag.infra.observability.fake_trace import FakeTrace
from tests.fakes.fake_vector_store import FakeVectorStore
from tests.fakes.fake_graph_store import FakeGraphStore


def _make_service(*, alpha: float = 1.0, beta: float = 1.0, normalization: bool = True) -> QueryService:
    return QueryService(
        vector_store=FakeVectorStore(),
        graph_store=FakeGraphStore(),
        embedder=FakeEmbeddingV2(),
        kernel=FakeKernel(),
        post_processor=DefaultRetrievalPostProcessor(),
        trace=FakeTrace(),
        fusion_alpha=alpha,
        fusion_beta=beta,
        enable_fusion_score_normalization=normalization,
    )


def _chunk(doc_id: str, chunk_id: str, score: float, source: str = "vector") -> RetrievedChunk:
    return RetrievedChunk(doc_id=doc_id, chunk_id=chunk_id, text=chunk_id, score=score, source=source)


# ---------------------------------------------------------------------------
# 1. _normalize_scores 单元测试
# ---------------------------------------------------------------------------

class TestNormalizeScores:
    def test_typical_range(self):
        svc = _make_service()
        result = svc._normalize_scores([0.2, 0.6, 1.0])
        assert result == pytest.approx([0.0, 0.5, 1.0])

    def test_all_equal_positive(self):
        svc = _make_service()
        result = svc._normalize_scores([5.0, 5.0, 5.0])
        assert result == pytest.approx([1.0, 1.0, 1.0])

    def test_all_zero(self):
        svc = _make_service()
        result = svc._normalize_scores([0.0, 0.0])
        assert result == pytest.approx([0.0, 0.0])


# ---------------------------------------------------------------------------
# 2. normalization 开启后 fusion_debug 字段验证
# ---------------------------------------------------------------------------

class TestFusionDebugWithNormalization:
    def setup_method(self):
        svc = _make_service(normalization=True)
        vector_chunks = [
            _chunk("d1", "c1", 0.3),
            _chunk("d2", "c2", 0.9),
        ]
        graph_chunks = [
            _chunk("d1", "c1", 2.0, "graph"),
            _chunk("d3", "c3", 5.0, "graph"),
        ]
        _, self.debug = svc._fuse_chunks(vector_chunks, graph_chunks)

    def test_normalization_enabled_flag(self):
        assert self.debug["normalization_enabled"] is True

    def test_normalization_method_is_minmax(self):
        assert self.debug["normalization_method"] == "minmax"

    def test_vector_and_graph_scores_in_range(self):
        for item in self.debug["chunks"]:
            assert 0.0 <= item["vector_score"] <= 1.0
            assert 0.0 <= item["graph_score"] <= 1.0

    def test_raw_scores_exist(self):
        for item in self.debug["chunks"]:
            assert "raw_vector_score" in item
            assert "raw_graph_score" in item


# ---------------------------------------------------------------------------
# 3. alpha/beta 在 normalization 开启后影响排序
# ---------------------------------------------------------------------------

class TestAlphaBetaSortingWithNormalization:
    """
    chunk_a: vector=0.9, graph=1.0
    chunk_b: vector=0.1, graph=10.0

    归一化后:
      vector: [1.0, 0.0]  (0.9→1.0, 0.1→0.0)
      graph:  [0.0, 1.0]  (1.0→0.0, 10.0→1.0)

    alpha=1.0, beta=0.1 → a=1.0, b=0.1 → chunk_a 优先
    alpha=0.1, beta=1.0 → a=0.1, b=1.0 → chunk_b 优先
    """

    def _run(self, alpha: float, beta: float):
        svc = _make_service(alpha=alpha, beta=beta, normalization=True)
        vector_chunks = [
            _chunk("d1", "a", 0.9),
            _chunk("d2", "b", 0.1),
        ]
        graph_chunks = [
            _chunk("d1", "a", 1.0, "graph"),
            _chunk("d2", "b", 10.0, "graph"),
        ]
        fused, _ = svc._fuse_chunks(vector_chunks, graph_chunks)
        return [c.chunk_id for c in fused]

    def test_vector_dominant_alpha(self):
        order = self._run(alpha=1.0, beta=0.1)
        assert order[0] == "a"

    def test_graph_dominant_beta(self):
        order = self._run(alpha=0.1, beta=1.0)
        assert order[0] == "b"

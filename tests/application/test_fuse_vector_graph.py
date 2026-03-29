from graph_rag.domain.models import RetrievedChunk
from tests.helpers import build_test_service


def test_fuse_chunks_deduplicates_same_chunk():
    service = build_test_service()

    vector_chunks = [
        RetrievedChunk(
            doc_id="doc1",
            chunk_id="chunk1",
            text="hello",
            score=0.8,
            source="vector",
        )
    ]
    graph_chunks = [
        RetrievedChunk(
            doc_id="doc1",
            chunk_id="chunk1",
            text="hello",
            score=1.5,
            source="graph",
        )
    ]

    fused_chunks, fusion_debug = service._fuse_chunks(vector_chunks, graph_chunks)

    assert len(fused_chunks) == 1
    assert fused_chunks[0] == RetrievedChunk(
        doc_id="doc1",
        chunk_id="chunk1",
        text="hello",
        score=2.3,
        source="hybrid",
    )

    assert fusion_debug["input"]["vector_count"] == 1
    assert fusion_debug["input"]["graph_count"] == 1
    assert fusion_debug["output"]["fusion_count"] == 1


def test_fuse_chunks_vector_only():
    service = build_test_service()

    vector_chunks = [
        RetrievedChunk(
            doc_id="doc1",
            chunk_id="chunk1",
            text="vector only",
            score=0.7,
            source="vector",
        )
    ]

    fused_chunks, fusion_debug = service._fuse_chunks(vector_chunks, [])

    assert len(fused_chunks) == 1
    assert fused_chunks[0].source == "vector"
    assert fused_chunks[0].score == 0.7

    item = fusion_debug["chunks"][0]
    assert item["vector_hit"] is True
    assert item["graph_hit"] is False
    assert item["vector_score"] == 0.7
    assert item["graph_score"] == 0.0
    assert item["final_score"] == 0.7


def test_fuse_chunks_graph_only():
    service = build_test_service()

    graph_chunks = [
        RetrievedChunk(
            doc_id="doc1",
            chunk_id="chunk1",
            text="graph only",
            score=1.2,
            source="graph",
        )
    ]

    fused_chunks, fusion_debug = service._fuse_chunks([], graph_chunks)

    assert len(fused_chunks) == 1
    assert fused_chunks[0].source == "graph"
    assert fused_chunks[0].score == 1.2

    item = fusion_debug["chunks"][0]
    assert item["vector_hit"] is False
    assert item["graph_hit"] is True
    assert item["vector_score"] == 0.0
    assert item["graph_score"] == 1.2
    assert item["final_score"] == 1.2


def test_fuse_chunks_hybrid_source_and_score():
    service = build_test_service()

    vector_chunks = [
        RetrievedChunk(
            doc_id="doc1",
            chunk_id="chunk1",
            text="same",
            score=0.6,
            source="vector",
        )
    ]
    graph_chunks = [
        RetrievedChunk(
            doc_id="doc1",
            chunk_id="chunk1",
            text="same",
            score=1.4,
            source="graph",
        )
    ]

    fused_chunks, _ = service._fuse_chunks(vector_chunks, graph_chunks)

    assert len(fused_chunks) == 1
    assert fused_chunks[0].source == "hybrid"
    assert fused_chunks[0].score == 2.0


def test_fuse_chunks_sorts_by_final_score_desc():
    service = build_test_service()

    vector_chunks = [
        RetrievedChunk("doc1", "chunk1", "a", 0.3, "vector"),
        RetrievedChunk("doc1", "chunk2", "b", 0.9, "vector"),
    ]
    graph_chunks = [
        RetrievedChunk("doc1", "chunk1", "a", 1.0, "graph"),
    ]

    fused_chunks, _ = service._fuse_chunks(vector_chunks, graph_chunks)

    assert [c.chunk_id for c in fused_chunks] == ["chunk1", "chunk2"]
    assert fused_chunks[0].score == 1.3
    assert fused_chunks[1].score == 0.9


def test_query_service_retrieval_debug_contains_fusion():
    service = build_test_service()

    result = service.query(
        query="test query",
        top_k=5,
        enable_vector=True,
        enable_graph=True,
    )

    assert "fusion" in result.retrieval_debug
    assert "input" in result.retrieval_debug["fusion"]
    assert "output" in result.retrieval_debug["fusion"]
    assert "chunks" in result.retrieval_debug["fusion"]
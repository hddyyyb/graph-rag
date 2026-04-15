from graph_rag.infra.adapters import FixedLengthChunker, FixedClock
from graph_rag.infra.observability.logging import SimpleTrace
from tests.helpers import build_test_ingest_service


class CaptureTrace(SimpleTrace):
    '''只在测试里做一个CaptureTrace，继承SimpleTrace，
    重写event()，一边记录、一边保留原日志行为。'''
    def __init__(self, clock):
        super().__init__(clock=clock)
        self.events = []

    def event(self, name: str, **fields):
        self.events.append((name, fields))
        super().event(name, **fields)


def test_ingest_emits_chunk_quality_event():
    clock = FixedClock("2000-01-01T00:00:00Z")
    trace = CaptureTrace(clock=clock)
    service = build_test_ingest_service(
        trace=trace,
        chunker=FixedLengthChunker(chunk_size=10, chunk_overlap=0)
        )

    text = "This is a test document. " * 20

    result = service.ingest(
        doc_id="doc_test",
        text=text,
    )

    assert result.chunks > 0

    event_names = [e[0] for e in trace.events]

    # 关键断言：Day31新增能力
    assert "chunk_quality" in event_names

    # 可选：验证字段存在
    quality_events = [e for e in trace.events if e[0] == "chunk_quality"]
    assert len(quality_events) == 1

    payload = quality_events[0][1]

    assert "chunk_count" in payload
    assert "min_length" in payload
    assert "max_length" in payload
    assert "avg_length" in payload
    '''        self.trace.event(
            "chunk_quality",
            chunk_count=chunk_count,
            min_length=min_length,
            max_length=max_length,
            avg_length=avg_length,
        )'''
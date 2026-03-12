from __future__ import annotations
from typing import Any, Dict

from graph_rag.ports.observability import TracePort

class FakeTrace(TracePort):
    def __init__(self) -> None:
        self._trace_id = "trace_test_999"
        self._fields = {}

    def get_trace_id(self) -> str:
        return self._trace_id

    def set_trace_id(self, trace_id: str) -> None:
        self._trace_id = trace_id

    def bind(self, **fields: Any) -> None:
        self._fields.update(fields)

    def event(self, name: str, **fields: Any) -> None:
        pass

    def get_bound_fields(self) -> Dict[str, Any]:
        return dict(self._fields)
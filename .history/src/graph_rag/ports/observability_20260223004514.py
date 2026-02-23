from __future__ import annotations

from typing import Any, Dict, Protocol


class TracePort(Protocol):
    def get_trace_id(self) -> str:
        ...

    def set_trace_id(self, trace_id: str) -> None:
        ...

    def bind(self, **fields: Any) -> None:
        ...

    def event(self, name: str, **fields: Any) -> None:
        ...

    def get_bound_fields(self) -> Dict[str, Any]:
        ...
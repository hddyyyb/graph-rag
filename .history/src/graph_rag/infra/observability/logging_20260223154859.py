from __future__ import annotations

import contextvars
import logging
import sys
import uuid
from typing import Any, Dict

from graph_rag.ports.observability import TracePort

_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")  # 存当前上下文的trace_id字符串
_bound_fields_var: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "bound_fields", default=None
)
# 但这里有个小坑：default={}是可变对象，理论上不推荐（虽然ContextVar的行为会让它没那么容易出大事，但仍建议用default=None更稳，然后每次get后创建新dict）。

class SimpleTrace(TracePort):    # 这是Ports层接口的Infra实现
    def get_trace_id(self) -> str:
        tid = _trace_id_var.get()
        if not tid:
            tid = uuid.uuid4().hex
            _trace_id_var.set(tid)
        return tid

    def set_trace_id(self, trace_id: str) -> None:
        _trace_id_var.set(trace_id or uuid.uuid4().hex)

    def bind(self, **fields: Any) -> None:
        cur = dict(_bound_fields_var.get() or {})
        cur.update(fields)
        _bound_fields_var.set(cur)

    def event(self, name: str, **fields: Any) -> None:
        logger = logging.getLogger("graph_rag")
        payload = {
            "event": name,
            "trace_id": self.get_trace_id(),
            **(self.get_bound_fields() or {}),
            **fields,
        }
        logger.info("event=%s payload=%s", name, payload)

    def get_bound_fields(self) -> Dict[str, Any]:
        return dict(_bound_fields_var.get() or {})


def setup_logging(level: str = "INFO") -> None:
    logger = logging.getLogger("graph_rag")
    logger.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s trace_id=%(trace_id)s %(message)s"
    )
    handler.setFormatter(fmt)

    class TraceIdFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            record.trace_id = _trace_id_var.get() or "-"
            return True

    handler.addFilter(TraceIdFilter())

    # avoid duplicate handlers under reload
    logger.handlers = []
    logger.addHandler(handler)
    logger.propagate = False
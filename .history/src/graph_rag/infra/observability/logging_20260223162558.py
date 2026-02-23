from __future__ import annotations

import contextvars
import logging
import sys
import uuid
from typing import Any, Dict

from graph_rag.ports.observability import TracePort

_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")  # contextvars保证：每个协程有自己的trace_id, 线程安全, 异步安全
_bound_fields_var: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "bound_fields", default={}
)  # 每个请求独立的小字典,存系统里想追踪的上下文：比如doc_id、user_id、query、tenant等, 因为是ContextVar所以不同HTTP请求之间不会互相串数据


class SimpleTrace(TracePort):    # 这是Ports层接口的Infra实现
    def get_trace_id(self) -> str:
        tid = _trace_id_var.get()
        if not tid:
            tid = uuid.uuid4().hex
            _trace_id_var.set(tid)
        return tid

    def set_trace_id(self, trace_id: str) -> None:
        _trace_id_var.set(trace_id or uuid.uuid4().hex)

    def bind(self, **fields: Any) -> None:    # 绑定上下文字段, 后续所有日志都会带这个字段
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
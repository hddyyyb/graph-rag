from __future__ import annotations

from typing import Any, Dict, Protocol



'''
系统“如何记录和传播trace信息”的抽象接口。
也就是说：Application层想记录日志、trace_id、事件时，
它不应该依赖logging库、OpenTelemetry、Sentry等具体实现。
它只依赖这个Port。
'''
class TracePort(Protocol):
    def get_trace_id(self) -> str:    # 获取当前请求的trace_id
        ...

    def set_trace_id(self, trace_id: str) -> None:    # 设置trace_id（通常在middleware里设置）
        ...

    def bind(self, **fields: Any) -> None:    # 绑定一些上下文字段，比如trace.bind(doc_id="doc1"),之后所有event都会带上doc_id。
        ...

    def event(self, name: str, **fields: Any) -> None:  # 记录一次结构化事件: trace.event("query_start", enable_graph=True)
        ...

    def get_bound_fields(self) -> Dict[str, Any]:  # 获取当前绑定的字段（调试用）
        ...
    

    '''
        Application层不应该写:
            import logging
            logging.info(...)
        那样你以后换：
        OpenTelemetry,Jaeger,Datadog,ELK,结构化JSON日志
        都会影响Application层。
        有了TracePort, Application只做
            self.trace.event(...)
        Infra层决定怎么记录。
'''
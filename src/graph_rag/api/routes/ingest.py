from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from graph_rag.api.schemas.ingest import IngestRequest, IngestResponse
from graph_rag.application.ingest_service import IngestService
from graph_rag.infra.config.settings import Settings
from graph_rag.ports.observability import TracePort

router = APIRouter()


def get_container(request: Request):
    return request.app.state.container


def get_ingest_service(request: Request) -> IngestService:
    return request.app.state.container["ingest_service"]


def get_trace(request: Request) -> TracePort:
    return request.app.state.container["trace"]


def get_settings(request: Request) -> Settings:
    return request.app.state.container["settings"]


# 下面发生了数据格式检查
@router.post("/ingest", response_model=IngestResponse)  
def ingest(
    payload: IngestRequest,
    svc: IngestService = Depends(get_ingest_service),
    trace: TracePort = Depends(get_trace),
) -> IngestResponse:
    res = svc.ingest(doc_id=payload.doc_id, text=payload.text, metadata=payload.metadata)
    return IngestResponse(doc_id=res.doc_id, chunks=res.chunks, trace_id=trace.get_trace_id())



'''
类型检测发生在
    payload: IngestRequest
也就是：
    def ingest(
        payload: IngestRequest,
而不是在函数体里
'''
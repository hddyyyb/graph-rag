from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from graph_rag.api.schemas.query import QueryRequest, QueryResponse
from graph_rag.application.query_service import QueryService
from graph_rag.ports.observability import TracePort

router = APIRouter()


def get_query_service(request: Request) -> QueryService:
    return request.app.state.container["query_service"]


def get_trace(request: Request) -> TracePort:
    return request.app.state.container["trace"]


@router.post("/query", response_model=QueryResponse)
def query(
    payload: QueryRequest,
    svc: QueryService = Depends(get_query_service),
    trace: TracePort = Depends(get_trace),
) -> QueryResponse:
    ans = svc.query(
        query=payload.query,
        top_k=payload.top_k,
        enable_graph=payload.enable_graph,
        enable_vector=payload.enable_vector,
    )
    # ans.trace_id应与trace一致
    return QueryResponse(
        answer=ans.answer,
        trace_id=ans.trace_id,
        retrieval_debug=ans.retrieval_debug,
        citations=ans.citations,
    )
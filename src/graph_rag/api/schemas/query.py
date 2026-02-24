from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=None, ge=1, le=50)
    enable_graph: bool = True
    enable_vector: bool = True


class QueryResponse(BaseModel):
    answer: str
    trace_id: str
    retrieval_debug: Dict[str, Any]
    citations: Optional[List[Dict[str, Any]]] = None



'''
    定义/query接口的请求体与响应体数据结构(HTTP层用)
    QueryRequest: query、top_k、enable_graph、enable_vector
    QueryResponse: answer、trace_id、retrieval_debug、citations
'''
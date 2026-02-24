from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    doc_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class IngestResponse(BaseModel):
    doc_id: str
    chunks: int
    trace_id: str



'''
定义/ingest接口的请求体与响应体数据结构(HTTP层用)
IngestRequest: 客户端要传什么字段(doc_id、text、metadata)  
    因为在api层调用注入的时候, res = svc.ingest(doc_id=payload.doc_id, text=payload.text, metadata=payload.metadata)
IngestResponse:服务端返回什么(doc_id、chunks、trace_id)
用的是Pydantic的BaseModel, 能自动校验类型和必填字段
'''
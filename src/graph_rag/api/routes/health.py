from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


'''
定义/health路由, 用于健康检查:
GET /health返回{"status":"ok"}
'''
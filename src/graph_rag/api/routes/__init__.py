from .health import router as health_router
from .ingest import router as ingest_router
from .query import router as query_router

# 出口文件：把各个router统一导出，方便在main.py里include
__all__ = ["health_router", "ingest_router", "query_router"]
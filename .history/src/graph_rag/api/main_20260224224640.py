from __future__ import annotations

import uuid
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from graph_rag.api.routes import health_router, ingest_router, query_router
from graph_rag.domain.errors import (
    ConflictError,
    DependencyError,
    NotFoundError,
    ValidationError,
)
from graph_rag.infra.adapters import (
    HashEmbeddingProvider,
    InMemoryGraphStore,
    InMemoryVectorStore,
    SimpleKernel,
)
from graph_rag.infra.config import Settings
from graph_rag.infra.observability.logging import SimpleTrace, setup_logging


# api/main.py 这是FastAPI应用入口, 负责"把系统装配起来并跑起来"


def build_container() -> Dict[str, Any]:  # 创建DI容器（settings、trace、stores、services等实例）
    settings = Settings()                 # 2.1 Settings与日志初始化, 通常是配置入口：默认值、环境变量读取（你注释里Day2/Day3暗示后续会从env加载）
    setup_logging(settings.log_level)     # 把日志系统按配置初始化
                                          # 关键点：日志初始化要尽早做，
                                          # 因为后面构造组件/处理请求都要记录日志。

    trace = SimpleTrace()                 # 2.2 Trace对象：请求链路的“上下文”

    # Adapters (Day2 memory)    2.3 Adapters：基础设施层的实现（此处是内存版）
    # 这一层叫Adapters很典型：
    # 让上层服务依赖抽象接口，而不是依赖具体实现。
    # 你现在用InMemory实现，
    # 未来可以无缝换成Milvus/FAISS/Neo4j/PGVector/真实Embedding API等。
    vector_store = InMemoryVectorStore()
    graph_store = InMemoryGraphStore()
    embedder = HashEmbeddingProvider(dim=32)
    kernel = SimpleKernel()

    # Application services  2.4 Application services：业务用例层（Ingest/Query）
    from graph_rag.application import IngestService, QueryService

    # 把文档/文本摄入→切块→embedding→写入vector store→抽取图→写入graph store
    ingest_service = IngestService(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        trace=trace,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    # 查询→向量召回+图召回→融合→交给kernel生成回答
    query_service = QueryService(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        kernel=kernel,
        trace=trace,
        vector_top_k=settings.vector_top_k,
        graph_top_k=settings.graph_top_k,
    )

    # 返回容器字典
    # 把所有实例放入一个dict，后面放到app.state.container中供路由/中间件读取
    return {
        "settings": settings,
        "trace": trace,
        "vector_store": vector_store,
        "graph_store": graph_store,
        "embedder": embedder,
        "kernel": kernel,
        "ingest_service": ingest_service,
        "query_service": query_service,
    }


def create_app() -> FastAPI:    # 构建FastAPI实例并挂载所有东西
    app = FastAPI(title="GraphRAG", version="0.1.0")

    # Build DI container
    # app.state是FastAPI提供的全局状态对象（本质上是挂在app实例上的一个容器）
    # 把“DI容器”塞进去，就能在任意请求里通过request.app.state.container拿到服务实例
    app.state.container = build_container()  

    # Trace middleware: ensure every request has trace_id (header -> contextvar -> response header)
    @app.middleware("http")
    async def trace_middleware(request: Request, call_next):        # 每个请求进来设置trace_id，并写回响应header
        trace = request.app.state.container["trace"]                # 1. 从容器取trace
        incoming = request.headers.get("x-trace-id", "").strip()    # 2. 读请求头x-trace-id
        trace_id = incoming or uuid.uuid4().hex
        trace.set_trace_id(trace_id)

        response = await call_next(request)
        response.headers["x-trace-id"] = trace.get_trace_id()
        return response

    # Exception mapping
    @app.exception_handler(ValidationError)    # 把Domain异常映射成HTTP状态码+JSON
    async def handle_validation(_: Request, exc: ValidationError):
        return JSONResponse(status_code=400, content={"error": "validation_error", "message": str(exc)})

    @app.exception_handler(NotFoundError)
    async def handle_not_found(_: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"error": "not_found", "message": str(exc)})

    @app.exception_handler(ConflictError)
    async def handle_conflict(_: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"error": "conflict", "message": str(exc)})

    @app.exception_handler(DependencyError)
    async def handle_dependency(_: Request, exc: DependencyError):
        return JSONResponse(status_code=502, content={"error": "dependency_error", "message": str(exc)})

    @app.exception_handler(Exception)
    async def handle_unknown(request: Request, exc: Exception):
        trace = request.app.state.container["trace"]
        trace.event("unhandled_exception", path=str(request.url.path), err=str(exc))
        return JSONResponse(status_code=500, content={"error": "internal_error", "message": "internal error"})

    # Routes   include_router 把/health、/ingest、/query挂上去
    app.include_router(health_router, tags=["health"]) 
    app.include_router(ingest_router, tags=["ingest"])
    app.include_router(query_router, tags=["query"])

    return app


app = create_app()    # 最后app = create_app()给uvicorn用
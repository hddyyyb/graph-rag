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

from neo4j import GraphDatabase

from graph_rag.infra.adapters import (
    HashEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    FakeEmbeddingV2,
    InMemoryGraphStore,
    Neo4jGraphStore,
    InMemoryVectorStore,
    SQLiteVectorStore,
    SimpleKernel,
    SimpleRAGKernel,
    SystemClock,
    FixedClock,
    FakeLLM,
    LocalLLM,
    DefaultRetrievalPostProcessor,
    FixedLengthChunker,
    RecursiveChunker,
)
from graph_rag.infra.document_loaders import SimpleDocumentLoader

from graph_rag.application import IngestService, QueryService

from graph_rag.infra.config import Settings
from graph_rag.infra.observability.logging import SimpleTrace, setup_logging


# api/main.py 这是FastAPI应用入口, 负责"把系统装配起来并跑起来"


def build_graph_store(settings: Settings):
    backend = settings.graph_store_backend.lower()

    if backend == "memory":
        graph_store = InMemoryGraphStore(
            expand_per_term_limit=settings.graph_expand_per_term_limit,
            direct_hit_weight=settings.graph_direct_hit_weight,
            expanded_hit_weight=settings.graph_expanded_hit_weight,
            max_expanded_terms=settings.graph_max_expanded_terms,
        )
        return graph_store

    if backend == "neo4j":
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
        return Neo4jGraphStore(
            driver=driver,
            database=settings.neo4j_database,
            ensure_schema_on_init=True,
            expand_per_term_limit=settings.graph_expand_per_term_limit,
            direct_hit_weight=settings.graph_direct_hit_weight,
            expanded_hit_weight=settings.graph_expanded_hit_weight,
            max_expanded_terms=settings.graph_max_expanded_terms,
        )

    raise ValueError(f"Unsupported graph_store_backend: {settings.graph_store_backend}")


def build_settings(settings_override: dict | None = None) -> Settings:
    return Settings(**(settings_override or {}))

def build_chunker(settings: Settings):
    chunking_strategy = settings.chunking_strategy
    if chunking_strategy == "fixed":
        return FixedLengthChunker(
            chunk_size=settings.chunk_size, 
            chunk_overlap=settings.chunk_overlap,
            )
    elif chunking_strategy == "recursive":
        return RecursiveChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    else:
        raise ValueError(f"unknown chunking strategy: {chunking_strategy}")
    
    
    
def build_container(settings: Settings) -> Dict[str, Any]: 
    # 创建DI容器（settings、trace、stores、services等实例）
    setup_logging(settings.log_level)     # 把日志系统按配置初始化, 日志初始化要尽早做, 因为后面构造组件/处理请求都要记录日志。

    clock = SystemClock()
    chunker = build_chunker(settings)

    # 第一步：先实例化底层基础组件（Clock、Trace、PostProcessor、LLM、Stores、Embedder等），这些组件没有业务逻辑，主要负责和外部系统交互（数据库、embedding API、LLM API等）。
    trace = SimpleTrace(clock = clock)                 # 2.2 Trace对象：请求链路的“上下文”

    post_processor = DefaultRetrievalPostProcessor()

    llm_backend = settings.llm_backend
    if llm_backend == "fake":
        llm = FakeLLM()
    elif llm_backend == "local":
        llm = LocalLLM(
            base_url=settings.local_llm_base_url,
            model=settings.local_llm_model,
        )
    elif llm_backend == "openai":
        from graph_rag.infra.adapters import OpenAILLM
        llm = OpenAILLM(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            instructions=settings.openai_instructions,
        )
    else:
        raise ValueError(f"unknown llm_backend: {llm_backend}")

    # Adapters：基础设施层的实现（此处是内存版）
    # 让上层服务依赖抽象接口，而不是依赖具体实现。
    # InMemory-> Milvus/FAISS/Neo4j/PGVector/真实Embedding API等。

    vector_store_backend = settings.vector_store_backend

    if vector_store_backend == "sqlite":
        sqlite_path = settings.sqlite_path
        if not sqlite_path:
            raise ValueError("sqlite backend requires sqlite_path")
        vector_store = SQLiteVectorStore(sqlite_path)
    else:
        vector_store = InMemoryVectorStore()
    
    graph_store = build_graph_store(settings)
    
    embedding_backend = settings.embedding_backend
    if embedding_backend == 'sentence_transformer':
        embedder = SentenceTransformerEmbeddingProvider(
            model_name_or_path=settings.embedding_model_name_or_path,
            )
    elif embedding_backend == 'hash':
        embedder = HashEmbeddingProvider(dim=32)
    elif embedding_backend == 'fake':
        embedder = FakeEmbeddingV2()
    else:
        raise ValueError(f"unknown embedding_backend: {embedding_backend}")


    #kernel = SimpleKernel()
    kernel = SimpleRAGKernel(llm=llm)
    # Application services  2.4 Application services：业务用例层（Ingest/Query）

    document_loader = SimpleDocumentLoader()
    
    '''Service-- 对应 业务流程, 代码是port(父类的东西), 它的参数是实例化的从西, infra实现的'''
    # 第二步：再实例化 service（IngestService、QueryService），这些service负责实现核心业务逻辑（摄入流程、查询流程），它们依赖第一步实例化的基础组件/适配器来完成工作。
    # 把文档/文本摄入→切块→embedding→写入vector store→抽取图→写入graph store
    ingest_service = IngestService(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        trace=trace,
        chunker=chunker,
        document_loader=document_loader,
    )
    # 查询→向量召回+图召回→融合→交给kernel生成回答
    query_service = QueryService(
        vector_store=vector_store,
        graph_store=graph_store,
        embedder=embedder,
        kernel=kernel,
        trace=trace,
        post_processor = post_processor, 
        vector_top_k=settings.vector_top_k,
        graph_top_k=settings.graph_top_k,
        fusion_alpha=settings.fusion_alpha,
        fusion_beta=settings.fusion_beta,
    )

    # 第三步：把同一个 settings 也挂进 container 里，让service/路由都能访问到配置（比如chunk_size、top_k、后端选择等），这样就实现了全局配置中心的效果。
    # 返回容器字典
    # 把所有实例放入一个dict，后面放到app.state.container中供路由/中间件读取
    return {
        "settings": settings,
        "clock": clock,
        "trace": trace,
        "vector_store": vector_store,
        "graph_store": graph_store,
        "embedder": embedder,
        "ingest_service": ingest_service,
        "query_service": query_service,
        "llm": llm,
        "kernel": kernel,
    }


def create_app(settings_override: dict | None = None) -> FastAPI:
    settings = build_settings(settings_override) # 2.1 Settings与日志初始化, 通常是配置入口：默认值、环境变量读取（你注释里Day2/Day3暗示后续会从env加载）

    # Build DI container
    # app.state是FastAPI提供的全局状态对象（本质上是挂在app实例上的一个容器）
    # 把“DI容器”塞进去，就能在任意请求里通过request.app.state.container拿到服务实例
    container = build_container(settings)

    # 构建FastAPI实例并挂载所有东西
    app = FastAPI(title="GraphRAG", version="0.1.0")
    app.state.container = container   # 把我们构建好的容器挂到app.state.container里，供后续路由/中间件使用
    app.state.settings = settings     # 也可以单独挂settings，方便直接访问配置
    
    # Trace middleware: ensure every request has trace_id (header -> contextvar -> response header)
    # @app.middleware("http")-装饰器:把下面这个函数注册成“HTTP请求的中间件”，以后每次有HTTP请求进来，框架都会按流程自动执行它。
    @app.middleware("http")
    async def trace_middleware(request: Request, call_next):        # 每个请求进来设置trace_id，并写回响应header
        trace = request.app.state.container["trace"]                # 1. 从容器取trace
        incoming = request.headers.get("x-trace-id", "").strip()    # 2. 读请求头x-trace-id
        trace_id = incoming or uuid.uuid4().hex                     # 3. 如果没有就生成一个uuid
        trace.set_trace_id(trace_id)                                # 4. trace.set_trace_id(trace_id)写入上下文

        response = await call_next(request)                         # 5. 调用下游（路由）
        response.headers["x-trace-id"] = trace.get_trace_id()       # 6. 把trace_id写回响应头，便于前端/调用方串联日志
        return response

    # Exception mapping
    # 5）异常映射：把Domain异常变成统一HTTP响应
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
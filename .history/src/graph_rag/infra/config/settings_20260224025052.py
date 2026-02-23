from __future__ import annotations

from pydantic import BaseModel, Field


class Settings(BaseModel):    # 定义整个GraphRAG系统的配置对象
    app_name: str = "graph-rag"
    log_level: str = Field(default="INFO")

    # Retrieval defaults
    vector_top_k: int = 5
    graph_top_k: int = 5

    # 存储模式
    # Day2: use in-memory stores. Day3: switch to real Milvus/Neo4j via env.
    store_mode: str = Field(default="memory")  # "memory" | "milvus_neo4j"

    # 控制文档切块大小, Chunking
    chunk_size: int = 400
    chunk_overlap: int = 50


    '''
    Infra层
    ↓
    Settings
    ↓
    DI容器读取
    ↓
    注入Service
    '''
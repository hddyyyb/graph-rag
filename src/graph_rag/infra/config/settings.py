from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# Literal用于明确限制变量、参数或返回值只能是特定的几个字面值

class Settings(BaseModel):    # 定义整个GraphRAG系统的配置对象
    app_name: str = "graph-rag"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    # Retrieval defaults
    vector_top_k: int = Field(default=5, ge=1)  # ge = greater than or equal， 必须是 整数，且 ≥ 1
    graph_top_k: int = Field(default=5, ge=1)

    # 控制文档切块大小, Chunking
    chunk_size: int = Field(default=400, ge=1)
    chunk_overlap: int = Field(default=50, ge=0)

    # graph_store_backend: "neo4j" | "memory"
    graph_store_backend: Literal["memory", "neo4j"] = "memory"
    vector_store_backend: Literal["memory", "sqlite"] = "memory"

    sqlite_path: str = ":memory:"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "00000000"
    neo4j_database: str | None = "neo4j"

    llm_backend: Literal["fake", "local", "openai"] = "fake"
    local_llm_base_url: str = "http://localhost:11434"
    local_llm_model: str = "llama3"

    openai_api_key: str | None = None
    openai_model: str = "gpt-5"
    openai_instructions: str = "You are a helpful assistant."


    '''👉 单个字段清洗
    例子:Settings(graph_store_backend="SQLite ")
    1. 先进入 normalize_lower()
    2. 变成 "sqlite"
    3. 再做类型校验'''
    @field_validator(
        "log_level",
        "graph_store_backend",
        "vector_store_backend",
        "llm_backend",
        mode="before",
    )  # 对这4个字段，在“赋值之前”统一做处理，mode="before"-在 Pydantic 做类型检查之前执行
    @classmethod  # 这个函数属于类，而不是某个实例
    def normalize_lower(cls, v: str):    
        if isinstance(v, str):
            return v.strip().lower()
        return v




    '''多字段关系校验
    1. 所有字段解析完
    2. 所有 field_validator 执行完
    3. 进入 model_validator'''
    @model_validator(mode="after")    # 在整个对象构建完成后执行
    def validate_cross_fields(self):  # 这里不是 cls, 是 self（已经创建好的对象）
        if self.chunk_overlap >= self.chunk_size:  # overlap 不能大于 chunk_size
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        if self.vector_store_backend == "sqlite" and not self.sqlite_path:  # 如果你选了 sqlite，就必须提供路径
            raise ValueError("sqlite backend requires sqlite_path")

        if self.llm_backend == "openai" and not self.openai_api_key:  # 如果你选了 openai，就必须提供 api key
            raise ValueError("openai backend requires openai_api_key")

        return self
    '''
    main.py:
    settings_override
        ↓
    build_settings()
        ↓
    Settings对象（唯一配置源）
        ↓
    build_container(settings)
        ↓
    所有组件统一读取 settings
    '''

    '''
    Infra层
    ↓
    Settings
    ↓
    DI容器读取
    ↓
    注入Service
    '''


    '''用户输入（混乱、不可信）
        ↓
field_validator（清洗）
        ↓
model_validator（校验）
        ↓
得到一个“绝对可靠”的 Settings'''
from .embedding_provider import HashEmbeddingProvider
from .milvus_store import InMemoryVectorStore
from .neo4j_store import InMemoryGraphStore
from .llamaindex_kernel import SimpleKernel

__all__ = [
    "HashEmbeddingProvider",
    "InMemoryVectorStore",
    "InMemoryGraphStore",
    "SimpleKernel",
]



'''
作用：把所有adapter统一导出，方便DI容器导入。

让你在api/main.py里可以一次性写：
from graph_rag.infra.adapters import InMemoryVectorStore, InMemoryGraphStore, ...

本质也是包出口文件，提升可读性与组织性。
'''
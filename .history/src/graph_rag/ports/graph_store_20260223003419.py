from __future__ import annotations

from typing import List, Protocol

from graph_rag.domain.models import RetrievedChunk


class GraphStorePort(Protocol):
    def upsert_document(self, doc_id: str, chunks: List[str]) -> None:
        ...

    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        ...


'''
系统对“图存储能力”的抽象接口。

也就是说：

Application层如果想用“图检索”，
它需要图系统提供什么能力？
它规定图系统必须支持：

1 写入文档（用于构建图结构）
2 根据query进行检索

        VectorStore	        GraphStore
输入	embedding向量	     query文本
语义	相似度检索	          结构关系检索
返回	RetrievedChunk	     RetrievedChunk

系统对“图检索能力”的抽象契约，
保证Application层不依赖Neo4j，
并统一返回Domain对象以支持双通道融合。
'''
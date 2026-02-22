from __future__ import annotations

from typing import List, Protocol

from graph_rag.domain.models import RetrievedChunk


class GraphStorePort(Protocol):
    def upsert_document(self, doc_id: str, chunks: List[str]) -> None:
        ...

    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        ...


'''
它规定图系统必须支持：

1 写入文档（用于构建图结构）
2 根据query进行检索
'''
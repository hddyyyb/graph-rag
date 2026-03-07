from __future__ import annotations

from typing import Protocol, List

from graph_rag.domain.models import RetrievedChunk
from graph_rag.ports.postprocess_models import ProcessedResults


class RetrievalPostProcessorPort(Protocol):
    def process(self, chunks: List[RetrievedChunk], top_k: int) -> ProcessedResults:
        ...



'''
输入：原始检索结果列表 + top_k
输出：处理后的结果 + citations
'''


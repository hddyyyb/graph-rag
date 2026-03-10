from __future__ import annotations

from typing import List, Optional

from graph_rag.domain.models import RetrievedChunk
from graph_rag.ports.postprocess_models import ProcessedResults
from graph_rag.ports.retrieval_post_processor import RetrievalPostProcessorPort

'''
raw retrieval results
  -> sort
  -> deduplicate
  -> top_k trim
  -> return final results
  '''

'''
@dataclass(frozen=True)
class RetrievedChunk:
    doc_id: str
    chunk_id: str
    text: str
    score: float
    source: str
'''

class DefaultRetrievalPostProcessor(RetrievalPostProcessorPort):
    def process(self, chunks: List[RetrievedChunk], top_k: int, min_score: Optional[float]= None) -> ProcessedResults:
        # 1. 排序
        sorted_chunks  = sorted(chunks, key=lambda x: x.score, reverse=True)
        # 2. min_score过滤
        if min_score is not None:
            sorted_chunks = [c for c in sorted_chunks if c.score >= min_score]
        # 3. dedup
        seen = set()
        out: List[RetrievedChunk] = []
        for c in sorted_chunks:
            key = (c.doc_id, c.chunk_id, c.source)
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
        
        # 4. top_k
        out = out[:top_k]
        # 5.citations
        citations = [
            {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "source": c.source, "score": c.score}
            for c in out
        ]
        return ProcessedResults(chunks=out, citations=citations)
from __future__ import annotations

from typing import List

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
    def process(self, chunks: List[RetrievedChunk], top_k: int) -> ProcessedResults:
        
        sorted_chunks  = sorted(chunks, key=lambda x: x.score, reverse=True)

        seen = set()
        out: List[RetrievedChunk] = []
        for c in sorted_chunks:
            key = (c.doc_id, c.chunk_id, c.source)
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
        
        out = out[:top_k]

        citations = [
            {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "source": c.source, "score": c.score}
            for c in out
        ]
        return ProcessedResults(chunks=out, citations=citations)
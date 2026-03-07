from __future__ import annotations

from typing import List

from graph_rag.domain.models import RetrievedChunk
from graph_rag.ports.postprocess_models import ProcessedResults
from graph_rag.ports.retrieval_post_processor import RetrievalPostProcessorPort


class DefaultRetrievalPostProcessor(RetrievalPostProcessorPort):
    def process(self, chunks: List[RetrievedChunk], top_k: int) -> ProcessedResults:
        seen = set()
        out: List[RetrievedChunk] = []
        for c in chunks:
            key = (c.doc_id, c.chunk_id, c.source)
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
        out.sort(key=lambda x: x.score, reverse=True)
        citations = [
            {"doc_id": c.doc_id, "chunk_id": c.chunk_id, "source": c.source, "score": c.score}
            for c in out[:3]
        ]
        return ProcessedResults(chunks=out, citations=citations)
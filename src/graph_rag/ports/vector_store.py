from __future__ import annotations
from typing import List, Protocol, Optional
from graph_rag.domain.models import RetrievedChunk
from dataclasses import dataclass

@dataclass(frozen = True)
class SearchOptions:
    filter_doc_id: Optional[str] = None
    min_score: Optional[float] = None


def normalize_search_options(
        options: Optional[SearchOptions] = None,
        filter_doc_id: Optional[str] = None,
        min_score:Optional[float] = None,
        )-> SearchOptions:
    base = options or SearchOptions()
    return SearchOptions(
        filter_doc_id = filter_doc_id if filter_doc_id is not None else base.filter_doc_id, 
        min_score = min_score if min_score is not None else base.min_score
        )


class VectorStorePort(Protocol):
    def upsert(
            self, 
            doc_id: str, 
            chunks: List[str], 
            chunk_ids: List[str],
            embeddings: List[List[float]]
            ) -> None:
        ...

    def search(
            self,
            query_embedding: List[float],
            top_k: int,
            options: Optional[SearchOptions] = None,
            filter_doc_id: Optional[str] = None,
            min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        ...
from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field

from graph_rag.domain.models import RetrievedChunk


class GraphChunkDebug(BaseModel):
    chunk_id: str
    doc_id: str
    direct_terms: List[str] = Field(default_factory=list)
    expanded_terms: List[str] = Field(default_factory=list)
    direct_hit_count: int = 0
    expanded_hit_count: int = 0
    score: float = 0.0


class GraphSearchDebug(BaseModel):
    query: str = ""
    direct_terms: List[str] = Field(default_factory=list)
    expanded_terms: List[str] = Field(default_factory=list)
    chunks: List[GraphChunkDebug] = Field(default_factory=list)


class GraphSearchResult(BaseModel):
    hits: List[RetrievedChunk] = Field(default_factory=list)
    debug: GraphSearchDebug = Field(default_factory=GraphSearchDebug)
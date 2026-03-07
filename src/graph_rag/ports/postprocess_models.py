from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

from graph_rag.domain.models import RetrievedChunk


@dataclass(frozen=True)
class ProcessedResults:
    chunks: List[RetrievedChunk]
    citations: List[Dict[str, Any]]
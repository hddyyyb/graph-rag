from __future__ import annotations

from typing import Dict, List, Optional, Protocol, Any

from graph_rag.domain.models import RetrievedChunk
from graph_rag.domain.graph_models import ChunkGraphRecord
from graph_rag.domain.graph_debug_models import GraphSearchResult

class GraphStorePort(Protocol):
    def upsert_chunk_graphs(self, records: List[ChunkGraphRecord]) -> None:
        ...

    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        ...

    def get_last_debug(self) -> Optional[Dict[str, Any]]:
        ...

'''
If the Application layer intends to use "graph retrieval", the graph system must support:

1. Writing documents (used to build the graph structure)
2. Performing retrieval based on a query

        VectorStore           GraphStore
Input   embedding vectors     query text
Logic   similarity retrieval  structural relationship retrieval
Output  RetrievedChunk        RetrievedChunk
'''
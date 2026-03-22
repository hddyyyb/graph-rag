from __future__ import annotations

from dataclasses import dataclass 
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    name: str
    node_type: str = "keyword"


@dataclass(frozen=True)  
class GraphEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str = "co_occurrence"
    weight: float = 1.0


@dataclass(frozen=True)
class ChunkGraphRecord:
    chunk_id: str
    doc_id: str
    text: str
    terms: List[str] = None    # 表明抽取工作已经在GraphStore外面完成了
from __future__ import annotations

from typing import Protocol
from graph_rag.domain.models import Chunk

class ChunkerPort(Protocol):
    def chunk(self, text: str, parent_id: str) -> list[Chunk]:
        ...
        
# parent_id是最强约束, 因为：
# chunk必须属于某个父对象
# IngestService本来就应该知道当前文本属于哪个doc/source
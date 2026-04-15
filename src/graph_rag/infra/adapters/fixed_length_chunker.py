from graph_rag.domain.models import Chunk
from graph_rag.ports.chunker import ChunkerPort

class FixedLengthChunker(ChunkerPort):
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50) -> None:
        # chunk_overlap是重叠的长度
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    
    def chunk(self, text: str, parent_id: str) -> list[Chunk]:
        t = (text or "").strip()

        if not t:
            return []
        
        position = 0
        start = 0
        out: list[Chunk] = []
        n = len(t)
        step = max(self.chunk_size  - max(self.chunk_overlap, 0), 1)
        while start < n:
            chunk_text = t[start:start + self.chunk_size]
            out.append(
                Chunk(
                    chunk_id=f"{parent_id}#{position}",
                    text=chunk_text,
                    position=position,
                    parent_id=parent_id,
                    length=len(chunk_text),
                )
            )
            start += step
            position += 1
        return out
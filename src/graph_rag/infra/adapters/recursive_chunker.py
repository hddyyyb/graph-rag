from graph_rag.domain.models import Chunk
from graph_rag.ports.chunker import ChunkerPort

class RecursiveChunker(ChunkerPort):
    # v1 recursive chunking keeps the same constructor shape as fixed chunking.
    # chunk_overlap is reserved for future support and is not applied yet.
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        #self.separators = ["\n\n", "\n", ".", " "]
        self.separators = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "]
    
    def chunk(self, text: str, parent_id: str) -> list[Chunk]:
        t = (text or "").strip()
        if not t:
            return []
        
        pieces = self._split_recursive(t, self.separators)

        # 把pieces拼成chunk_size的块
        chunks = []
        current = ""

        for piece in pieces:
            if not piece:
                continue
            if len(current) + len(piece) <= self.chunk_size:
                current += piece
            else:
                if current:
                    chunks.append(current)
                current = piece

        if current:
            chunks.append(current)
        
        return [
            Chunk(
                chunk_id=f"{parent_id}#{i}",
                text=c,
                position=i,
                parent_id=parent_id,
                length=len(c),
            )
            for i, c in enumerate(chunks)
        ]

    # 递归切分逻辑, 按照 ["\n\n", "\n", ".", " "]
    # 先"\n\n"分，如果一块大于chunk_size，这个大段中按照"\n"分，以此类推
    def _split_recursive(self, text: str, seps: list[str]) -> list[str]:
        
        # Step 1：终止条件
        if len(text) <= self.chunk_size:
            return [text]

        # Step 2：如果没有分隔符了 → fallback
        if not seps:
            return [text[i:i+self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        # Step 3：尝试当前分隔符
        sep = seps[0]

        if sep in text:
            parts = text.split(sep)

            # 变成“带分隔符的parts”
            merged_parts = []
            for i, part in enumerate(parts):
                if not part:
                    continue
                if i < len(parts) - 1:
                    merged_parts.append(part + sep)
                else:
                    merged_parts.append(part)

            results = []

            for part in merged_parts:

                if len(part) > self.chunk_size:
                    results.extend(self._split_recursive(part, seps[1:]))
                else:
                    results.append(part)

            return results
        
        # Step 4：如果当前分隔符切不了 → 换下一个
        return self._split_recursive(text, seps[1:])
from graph_rag.infra.adapters import (
    FixedLengthChunker, 
    RecursiveChunker
    )
from graph_rag.evaluation.models import EvalSample

text = """东方大陆的极东一角，是地图上唯一一块只有界线，却没有注明的区域。人们称这里为流星街。
    绝大部分人眼中，这是一片杳无人烟的荒土，被千年的垃圾所覆盖。
    部分情报资源优势者知道，这里是有人生存的，而且数量不少，以垃圾回收为生。
    一些身处高位却见不得光的人知道更多——这里有很多人，很多优秀的人，用食品药物和重金属就可以买到的“人材”。
    但只有身处流星街的人，才真正了解这里——
    这里是流星街，容许种种丢弃的地方，群星坠落之地。"""

chunker = RecursiveChunker(chunk_size=100, chunk_overlap=0)
chunks = chunker.chunk(text, parent_id="doc1")
for chunk in chunks:
    print("------")
    print("chunk_id:", chunk.chunk_id)
    print("position:", chunk.position)
    print("length:", chunk.length)
    print("preview:", chunk.text[:100])

samples = [
    EvalSample(
        query="流星街在外界眼中是什么地方？",
        relevant_chunk_ids=["doc1#0"],
    ),
    EvalSample(
        query="流星街的人主要依靠什么方式生存？",
        relevant_chunk_ids=["doc1#1"],
    ),
    EvalSample(
        query="流星街真正是什么样的地方？",
        relevant_chunk_ids=["doc1#2"],
    ),
]
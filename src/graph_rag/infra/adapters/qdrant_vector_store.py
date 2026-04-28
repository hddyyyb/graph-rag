from __future__ import annotations

import uuid
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from graph_rag.domain.models import RetrievedChunk
from graph_rag.ports.vector_store import SearchOptions, normalize_search_options

# 这个类把你系统里的 VectorStorePort 操作，翻译成 Qdrant 的 collection / point / vector / payload 操作。

def _point_id(doc_id: str, chunk_id: str) -> str:
    # 给每个chunk生成一个稳定ID, 同一个chunk(doc_id,chunk_id)重复写入，会覆盖同一个point，不会无限新增重复数据
    # Deterministic UUID so re-ingesting the same chunk overwrites the same point.
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}\x00{chunk_id}"))

'''我实现的QdrantVectorStore本质上是一个VectorStorePort适配器。

在写入阶段，它把每个chunk embedding转换成Qdrant point，vector保存embedding，payload保存doc_id、chunk_id和text，并用doc_id+chunk_id生成稳定UUID，保证重复摄入时可以覆盖同一条记录。

在查询阶段，它用query embedding调用Qdrant的query_points做cosine similarity检索，再把结果转换回系统统一的RetrievedChunk结构。因此QueryService不需要感知底层是SQLite还是Qdrant。'''

class QdrantVectorStore:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6334,
        collection_name: str = "graph_rag",
    ) -> None:
        # 创建一个连接Qdrant的客户端
        self._client = QdrantClient(
            host=host, 
            port=port,
            prefer_grpc=True,  # HTTP (6333), gRPC (6334)
            check_compatibility=False, # avoid version-check issues in local/proxy env
            )
        self._collection = collection_name
        self._vector_size: Optional[int] = None  # resolved on first upsert

    # Qdrant里必须先有collection，才能存向量。collection可以理解成一张向量表
    def _ensure_collection(self, vector_size: int) -> None:
        collections = self._client.get_collections().collections
        collection_names = {c.name for c in collections}

        if self._collection not in collection_names:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            ) # 第一次upsert时，根据embedding长度创建collection
            # 并设置距离度量为Cosine

    # 这是写入流程
    def upsert(
        self,
        doc_id: str,
        chunk_ids: List[str],
        chunks: List[str],
        embeddings: List[List[float]],
    ) -> None:
        if not (len(chunk_ids) == len(chunks) == len(embeddings)):
            raise ValueError(
                f"chunk_ids, chunks and embeddings length mismatch: "
                f"{len(chunk_ids)} != {len(chunks)} != {len(embeddings)}"
            )
        if not embeddings:  # 没有embedding就不写
            return

        if self._vector_size is None:
            self._ensure_collection(len(embeddings[0]))  # 第一次写入时创建collection
            self._vector_size = len(embeddings[0])

        # Replace all chunks for this doc (mirrors SQLite DELETE + INSERT behavior).
        # 关键：它会先删除当前doc_id对应的旧chunk。
        self._client.delete(
            collection_name=self._collection,
            points_selector=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            ),
        )

        points = [
            PointStruct(
                id=_point_id(doc_id, chunk_id),
                vector=emb,
                payload={"doc_id": doc_id, "chunk_id": chunk_id, "text": text},
            ) # 每个chunk会变成一个Qdrant point
            for chunk_id, text, emb in zip(chunk_ids, chunks, embeddings)
        ]
        self._client.upsert(collection_name=self._collection, points=points)  # 写入Qdrant

    def search(
        self,
        query_embedding: List[float],
        top_k: int,
        options: Optional[SearchOptions] = None,
        filter_doc_id: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        opts = normalize_search_options(
            options=options,
            filter_doc_id=filter_doc_id,
            min_score=min_score,
        ) # 把filter_doc_id、min_score这些搜索条件统一处理

        if top_k <= 0:
            return []

        query_filter: Optional[Filter] = None
        if opts.filter_doc_id is not None:
            query_filter = Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=opts.filter_doc_id))]
            )  # 如果指定了doc_id，就只在某个文档里搜

        res = self._client.query_points(
            collection_name=self._collection,
            query=query_embedding,
            limit=top_k,
            query_filter=query_filter,
            score_threshold=opts.min_score,
            with_payload=True,
        )  # 这一步是真正的向量检索, 拿query_embedding去Qdrant里找最相似的top_k个chunk

        hits = res.points

        results = []
        for h in hits:
            payload = h.payload or {}

            # 然后把Qdrant结果转换成你系统统一的：RetrievedChunk(...)
            results.append(
                RetrievedChunk(
                    doc_id=payload.get("doc_id", ""),
                    chunk_id=payload.get("chunk_id", ""),
                    text=payload.get("text", ""),
                    score=float(h.score) if h.score is not None else 0.0,
                    source="qdrant",
                )
            )

        return results

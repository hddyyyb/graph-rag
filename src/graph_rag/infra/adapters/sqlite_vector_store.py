import sqlite3    # sqlite3 是 python 自带文件数据库，不需要安装

# 谁负责实例化 SQLiteVectorStore？
# 答：Composition Root（container装配逻辑）

import json, pickle
from typing import List, Optional
from graph_rag.domain.models import RetrievedChunk
import math

from graph_rag.ports.vector_store import SearchOptions, normalize_search_options


class SQLiteVectorStore:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)

        # 创建一张叫 chunks 的表
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                doc_id TEXT,
                chunk_id TEXT,
                text TEXT,
                embedding TEXT,
                PRIMARY KEY (doc_id, chunk_id)
            )
        """)
        self._conn.commit()
    
    def upsert(self, doc_id: str, chunks: List[str], embeddings: List[List[float]]) -> None:
        # 1. 校验长度一致
        if len(chunks) != len(embeddings):
            raise ValueError(f"chunks and embeddings length mismatch: {len(chunks)} != {len(embeddings)}")
        # 2. 删除旧数据
        self._conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        # 一次批量提交,数据库内部循环执行

        # 3. 插入新数据（用 executemany）
        rows = []
        for i in range(len(chunks)):
            chunk_id = f"{doc_id}#{i}"
            row = (doc_id, chunk_id, chunks[i], json.dumps(embeddings[i]))  
            # json.dumps()  把 Python 对象变成JSON字符串字符串, f""= formatted string（格式化字符串）
            # 规则: f"文字 {变量} 文字", Python 会自动把变量转成字符串。
            rows.append(row)
            
        self._conn.executemany("INSERT INTO chunks (doc_id, chunk_id, text, embedding) VALUES (?, ?, ?, ?)", rows)
        
        # 4. commit
        self._conn.commit()


   
    def search(
            self,
            query_embedding: List[float],
            top_k: int,
            options: Optional[SearchOptions] = None,
            filter_doc_id: Optional[str] = None,
            min_score: Optional[float] = None,
            ) -> List[RetrievedChunk]:
        
        opts = normalize_search_options(
            options = options, 
            filter_doc_id = filter_doc_id,
            min_score = min_score,
            )
        # TODO 1: 边界  
        if top_k <= 0:
            return []

        # TODO 2: 取数据

        if opts.filter_doc_id is None:
            cur = self._conn.execute(
                "SELECT doc_id, chunk_id, text, embedding FROM chunks"
                )
        else:
            cur = self._conn.execute(
                "SELECT doc_id, chunk_id, text, embedding FROM chunks WHERE doc_id = ?",
                (opts.filter_doc_id,),
            )
        rows = cur.fetchall()

        # TODO 3: 逐条算分
        scored: List[RetrievedChunk] = []
        for doc_id, chunk_id, text, emb_json in rows:
            emb = json.loads(emb_json)
            score = self._cosine(query_embedding, emb)
            if opts.min_score is not None and score < opts.min_score:
                continue
            scored.append(RetrievedChunk(
                doc_id=doc_id,
                chunk_id=chunk_id,
                text=text,
                score=score,
                source="sqlite",
            ))

        # TODO 4: 排序 + top_k
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    def _cosine(self, a: List[float], b: List[float]) -> float:
        # TODO: 纯python cosine，相同维度假设成立；分母0要保护
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)
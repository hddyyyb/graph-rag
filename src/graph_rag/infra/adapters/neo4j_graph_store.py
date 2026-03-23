from __future__ import annotations

from email.mime import text
from itertools import combinations
from typing import Iterable, List, Sequence, Any

from neo4j import Driver

from graph_rag.domain.models import RetrievedChunk
from graph_rag.domain.graph_models import ChunkGraphRecord

from graph_rag.ports.graph_store import GraphStorePort

from graph_rag.common.text_utils import extract_terms


class Neo4jGraphStore(GraphStorePort):
    """
    Minimal Neo4j-backed GraphStore implementation.

    Current responsibilities:
    - store chunk nodes
    - store term nodes
    - store Chunk -> Term mentions relations
    - store Term -> Term co-occurrence relations
    - search chunks by query-term matching

    Intentionally out of scope for Day24:
    - multi-hop graph reasoning
    - entity extraction pipeline
    - graph/vector fusion optimization
    - advanced ranking based on graph topology
    """
    def __init__(
        self,
        driver: Driver,
        database: str | None = None,
        ensure_schema_on_init: bool = True,
    ) -> None:
        self.driver = driver
        self.database = database

        if ensure_schema_on_init:
            self._ensure_schema()

    # -------------------------------------------------------------------------
    # public api
    # -------------------------------------------------------------------------
    
    def upsert_chunk_graphs(self, records: List[ChunkGraphRecord]) -> None:
        """
        👉 作用: 批量写入 chunk → 图
        Upsert chunk-level graph records into Neo4j.

        For each record:
        - MERGE Chunk
        - MERGE Terms
        - MERGE (Chunk)-[:MENTIONS]->(Term)
        - MERGE (Term)-[:CO_OCCURS_WITH]->(Term)

        Notes:
        - This is a minimal upsert strategy.
        - It does not aggressively delete stale relationships for existing chunk_ids.
        - If later you need strict replacement semantics, you can add:
          delete old MENTIONS edges for the chunk before rebuilding them.
        """
        if not records:
            return

        with self.driver.session(database=self.database) as session:
            for record in records:
                terms = self._get_terms_from_record(record)
                payload = {
                        "chunk_id": record.chunk_id,
                        "doc_id": record.doc_id,
                        "text": record.text,
                        "terms": terms,
                    }
                # 👉 session.execute_write(...) = Neo4j 事务执行
                # 👉 execute_write 开启一个写事务
                # 👉 _upsert_one_record_tx 是 transaction function
                # 👉 payload 是传给 transaction function 的参数
                session.execute_write(
                    self._upsert_one_record_tx,
                    payload,
                )

    
    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        """
        Search relevant chunks by matching extracted query terms against graph terms.

        Ranking strategy for Day24:
        - count how many distinct query terms hit each chunk
        """      
        if not query or top_k <= 0:
            return []

        terms = extract_terms(query)  # Step1: 提取 query terms
        if not terms:
            return []

        # Step2: session.execute_read 调用查询事务
        with self.driver.session(database=self.database) as session:
            rows = session.execute_read(
                self._search_chunks_by_terms_tx,
                {
                    "terms": terms,
                    "top_k": top_k,
                },
                )

        # Step3: 转成返回对象
        results: list[RetrievedChunk] = []
        for row in rows:
            results.append(
                RetrievedChunk(
                    chunk_id=row["chunk_id"],
                    doc_id=row["doc_id"],
                    text=row["text"],
                    score=float(row["score"]),
                    source="graph",
                )
            )  # ✔ source="graph", 是 multi-retrieval 的来源标记
        return results


    def close(self) -> None:
        """
        Optional helper if you want explicit lifecycle management.
        """
        self.driver.close()


    # -------------------------------------------------------------------------
    # schema
    # -------------------------------------------------------------------------


    def _ensure_schema(self) -> None:
        """
        Create minimal constraints for Neo4j graph storage.
        建 schema(非常重要)
        含义: Chunk 唯一, Term 唯一 
        因为后面 MERGE (c:Chunk {chunk_id: ...})
        没有唯一约束会重复建节点 
        """
        statements = [
            """
            CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
            FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT term_name_unique IF NOT EXISTS
            FOR (t:Term) REQUIRE t.name IS UNIQUE
            """,
        ]

        with self.driver.session(database=self.database) as session:
            for stmt in statements:
                session.run(stmt)
    

    # -------------------------------------------------------------------------
    # internal tx functions
    # -------------------------------------------------------------------------
    

    # transaction function（事务函数）: 在数据库事务里执行的一段函数
    @staticmethod
    def _upsert_one_record_tx(tx, payload: dict[str, Any]) -> None:
        '''
        transaction function 第一个参数一定是 tx
        代表数据库事务 transaction
        所有数据库操作都必须通过它: tx.run("Cypher语句")
        '''
        chunk_id = payload["chunk_id"]
        doc_id = payload["doc_id"]
        text = payload["text"]
        terms: list[str] = payload["terms"]

        # 1) upsert chunk node
        tx.run(
            """
            MERGE (c:Chunk {chunk_id: $chunk_id})
            SET c.doc_id = $doc_id,
                c.text = $text
            """,
            chunk_id=chunk_id,
            doc_id=doc_id,
            text=text,
        )
        # 👉 MERGE = 不存在就创建，存在就复用


        # 2) upsert term nodes + mentions edges
        for term in terms:
            tx.run(
                """
                MERGE (c:Chunk {chunk_id: $chunk_id})
                MERGE (t:Term {name: $term})
                MERGE (c)-[:MENTIONS]->(t)
                """,
                chunk_id=chunk_id,
                term=term,
            )
            # 表示: 这个 chunk 提到了这个 term

        # 3) upsert co-occurrence edges
        # only create one canonical direction: sorted(term1, term2)
        for term1, term2 in combinations(sorted(set(terms)), 2):
            tx.run(
                """
                MERGE (t1:Term {name: $term1})
                MERGE (t2:Term {name: $term2})
                MERGE (t1)-[r:CO_OCCURS_WITH]->(t2)
                ON CREATE SET r.weight = 1
                ON MATCH SET r.weight = r.weight + 1
                """,
                term1=term1,
                term2=term2,
            )
            # 两个词经常一起出现 → 强关系


    # transaction function（事务函数）: 在数据库事务里执行的一段函数
    # 查询的事务函数
    @staticmethod
    def _search_chunks_by_terms_tx(tx, payload: dict[str, Any]) -> list[dict[str, Any]]:
        terms: list[str] = payload["terms"]
        top_k: int = payload["top_k"]

        result = tx.run(
            """
            MATCH (c:Chunk)-[:MENTIONS]->(t:Term)
            WHERE t.name IN $terms
            WITH c, count(DISTINCT t) AS score
            ORDER BY score DESC, c.chunk_id ASC
            LIMIT $top_k
            RETURN c.chunk_id AS chunk_id,
                   c.doc_id AS doc_id,
                   c.text AS text,
                   score AS score
            """,
            terms=terms,
            top_k=top_k,
        )
        #  本质: 匹配 query 中多少个 term

        return [dict(record) for record in result]
    

    # -------------------------------------------------------------------------
    # term processing
    # -------------------------------------------------------------------------

    def _get_terms_from_record(self, record: ChunkGraphRecord) -> list[str]:
        """
        Prefer record.terms if available; otherwise extract from record.text.

        This helps you keep ingestion behavior aligned with your current
        ChunkGraphRecord design.
        """
        raw_terms = getattr(record, "terms", None)

        if raw_terms:
            return self._normalize_terms(raw_terms)

        return extract_terms(record.text)


    def _normalize_terms(self, terms: Iterable[str]) -> list[str]:
        # lower + strip + 去重
        seen: set[str] = set()
        normalized_terms: list[str] = []

        for term in terms:
            if term is None:
                continue

            value = str(term).strip().lower()
            value = self._strip_token(value)

            if not value:
                continue

            if value not in seen:
                seen.add(value)
                normalized_terms.append(value)

        return normalized_terms


    @staticmethod
    def _strip_token(token: str) -> str:
        return token.strip(" \t\r\n.,!?;:()[]{}<>\"'`“”‘’/\\|+-=*&#%@^~")
    


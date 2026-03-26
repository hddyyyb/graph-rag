from __future__ import annotations

from itertools import combinations
from typing import Dict, Iterable, List, Any, Optional

from neo4j import Driver

from graph_rag.domain.models import RetrievedChunk
from graph_rag.domain.graph_models import ChunkGraphRecord
from graph_rag.ports.graph_store import GraphStorePort
from graph_rag.common.text_utils import extract_terms


class Neo4jGraphStore(GraphStorePort):
    """
    Neo4j-backed GraphStore implementation.

    - store chunk nodes
    - store term nodes
    - store Chunk -> Term mentions relations
    - store Term -> Term co-occurrence relations
    - search chunks by query-term matching
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
        expand_per_term_limit: int = 2,
        direct_hit_weight: float = 1.0,
        expanded_hit_weight: float = 0.5,
        max_expanded_terms: int = 10,
    ) -> None:
        
        self.driver = driver
        self.database = database
        self.expand_per_term_limit = expand_per_term_limit
        self.direct_hit_weight = direct_hit_weight
        self.expanded_hit_weight = expanded_hit_weight
        self.max_expanded_terms = max_expanded_terms
        self._last_debug: Optional[Dict[str, Any]] = None
        
        if ensure_schema_on_init:
            self._ensure_schema()
    
    
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
    # public api
    # -------------------------------------------------------------------------
    def get_last_debug(self) -> Optional[Dict[str, Any]]:
        return self._last_debug
    

    def upsert_chunk_graphs(self, records: List[ChunkGraphRecord]) -> None:
        """
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
                # session.execute_write(...) = Neo4j 事务执行
                # execute_write 开启一个写事务
                # _upsert_one_record_tx 是 transaction function
                # payload 是传给 transaction function 的参数
                session.execute_write(
                    self._upsert_one_record_tx,
                    payload,
                )

    
    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        """
        Search relevant chunks by matching extracted query terms against graph terms.
        - count how many distinct query terms hit each chunk
        """      
        self._last_debug = None

        if not query or top_k <= 0:
            self._last_debug = {
                "query": query,
                "direct_terms": [],
                "expanded_terms": [],
                "chunks": [],
            }
            return []

        direct_terms  = extract_terms(query)
        if not direct_terms:
            self._last_debug = {
                "query": query,
                "direct_terms": [],
                "expanded_terms": [],
                "chunks": [],
            }
            return []

        expanded_terms = self._expand_terms(direct_terms)

        # session.execute_read 调用查询事务
        with self.driver.session(database=self.database) as session:
            direct_rows = session.execute_read(
                self._search_direct_hits_tx,
                {"terms": direct_terms},
                )
            
            expanded_rows: list[dict[str, Any]] = []
            if expanded_terms:
                expanded_rows = session.execute_read(
                    self._search_expanded_hits_tx,
                    {"terms": expanded_terms},
                )

        results = self._merge_rank_results(
            direct_rows = direct_rows,
            expanded_rows = expanded_rows,
            top_k = top_k
        )

        self._last_debug = self._build_debug_payload(
            query=query,
            direct_terms=direct_terms,
            expanded_terms=expanded_terms,
            direct_rows=direct_rows,
            expanded_rows=expanded_rows,
            results=results,
        )

        return results
    

    def _build_debug_payload(
        self,
        *,
        query: str,
        direct_terms: list[str],
        expanded_terms: list[str],
        direct_rows: list[dict[str, Any]],
        expanded_rows: list[dict[str, Any]],
        results: list[RetrievedChunk],
    ) -> dict[str, Any]:
        direct_map: dict[str, set[str]] = {}
        expanded_map: dict[str, set[str]] = {}

        for row in direct_rows:
            direct_map[row["chunk_id"]] = set(row.get("hit_terms", []))

        for row in expanded_rows:
            expanded_map[row["chunk_id"]] = set(row.get("hit_terms", []))

        chunks_debug: list[dict[str, Any]] = []

        for chunk in results:
            direct_hit_terms = sorted(direct_map.get(chunk.chunk_id, set()))
            expanded_hit_terms = sorted(expanded_map.get(chunk.chunk_id, set()))

            chunks_debug.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "direct_terms": direct_hit_terms,
                    "expanded_terms": expanded_hit_terms,
                    "direct_hit_count": len(direct_hit_terms),
                    "expanded_hit_count": len(expanded_hit_terms),
                    "score": chunk.score,
                }
            )

        return {
            "query": query,
            "direct_terms": sorted(direct_terms),
            "expanded_terms": sorted(expanded_terms),
            "chunks": chunks_debug,
        }
    

    def close(self) -> None:
        """
        Optional helper if you want explicit lifecycle management.
        """
        self.driver.close()


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

        # 1) upsert chunk node,  MERGE = 不存在就创建，存在就复用
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

        result = tx.run(
            """
            MATCH (c:Chunk)-[:MENTIONS]->(t:Term)
            WHERE t.name IN $terms
            WITH c, count(DISTINCT t) AS score
            ORDER BY score DESC, c.chunk_id ASC
            RETURN c.chunk_id AS chunk_id,
                   c.doc_id AS doc_id,
                   c.text AS text,
                   score AS score
            """,
            terms=terms,
        )
        #  本质: 匹配 query 中多少个 term

        return [dict(record) for record in result]
    

    @staticmethod
    def _expand_terms_tx(tx, payload: dict[str, Any]) -> list[dict[str, Any]]:
        '''
        输入 terms, per_term_limit
        输出 每个direct term扩展出来的候选term
        Python返回建议: 返回原始rows即可,后面Python拍平
        '''
        terms = payload["terms"]
        per_term_limit = payload["per_term_limit"]
        result = tx.run(
            """
            UNWIND $terms AS qterm
            MATCH (t1:Term {name: qterm})-[r:CO_OCCURS_WITH]-(t2:Term)
            WHERE NOT t2.name IN $terms
            WITH qterm, t2.name AS expanded_term, r.weight AS weight
            ORDER BY qterm, weight DESC, expanded_term ASC
            WITH qterm, collect({term: expanded_term, weight: weight}) AS candidates
            RETURN qterm, candidates[..$per_term_limit] AS expanded
            """,
            terms=terms,
            per_term_limit=per_term_limit,
        )
        return [dict(record) for record in result]
        # result 是 neo4j 的结果对象，不能直接用，转成 list[dict] 方便后续处理
        # result 的结构是:
        # [
        #   {
        #     "qterm": "term1",
        #     "expanded": [
        #       {"term": "expanded_term1", "weight": 5},
        #       {"term": "expanded_term2", "weight": 3},
        #     ]
        #   },
        #   {
        #     "qterm": "term2",
        #     "expanded": [
        #       {"term": "expanded_term3", "weight": 4},
        #     ]
        #   },
        # ]


    @staticmethod
    def _search_direct_hits_tx(tx, payload: dict[str, Any]) -> list[dict[str, Any]]:
        '''
        输入: terms
        输出: 每个term命中的chunk列表
        '''
        terms = payload["terms"]
        result = tx.run(
            """
            MATCH (c:Chunk)-[:MENTIONS]->(t:Term)
            WHERE t.name IN $terms
            WITH c, collect(DISTINCT t.name) AS hit_terms
            RETURN c.chunk_id AS chunk_id,
                c.doc_id AS doc_id,
                c.text AS text,
                hit_terms AS hit_terms
            """,
            terms=terms,
        )
        return [dict(record) for record in result]


    @staticmethod
    def _search_expanded_hits_tx(tx, payload: dict[str, Any]) -> list[dict[str, Any]]:
        terms = payload["terms"]
        result = tx.run(
            """
            MATCH (c:Chunk)-[:MENTIONS]->(t:Term)
            WHERE t.name IN $terms
            WITH c, collect(DISTINCT t.name) AS hit_terms
            RETURN c.chunk_id AS chunk_id,
                c.doc_id AS doc_id,
                c.text AS text,
                hit_terms AS hit_terms
            """,
            terms=terms,
        )
        return [dict(record) for record in result]
    

    # -------------------------------------------------------------------------
    # term processing
    # -------------------------------------------------------------------------

    def _merge_rank_results(
        self,
        direct_rows: list[dict[str, Any]],
        expanded_rows: list[dict[str, Any]],
        top_k: int,
    ) -> list[RetrievedChunk]:
        merged: dict[str, dict[str, Any]] = {}
        # direct_rows 是 dict list，每个 dict 代表一个 chunk，
        # 包含 chunk_id, doc_id, text, hit_terms（命中的 query term 列表）
        # ["chunk_id": ..., "doc_id": ..., "text": ..., "hit_terms": [...]], ...]
        # hit_terms 的 来源是: WITH c, collect(DISTINCT t.name) AS hit_terms 
        # 就是指 chunk c 命中了哪些 term, 而 collect 是把命中的 term 聚合成一个列表

        # 1. 聚合 direct hits 和 expanded hits
        for row in direct_rows:
            chunk_id = row["chunk_id"]
            merged.setdefault(
                chunk_id,
                {
                    "chunk_id": chunk_id,
                    "doc_id": row["doc_id"],
                    "text": row["text"],
                    "direct_terms": set(),
                    "expanded_terms": set(),
                },
            )
            merged[chunk_id]["direct_terms"].update(row.get("hit_terms", []))
        
        for row in expanded_rows:
            chunk_id = row["chunk_id"]
            merged.setdefault(
                chunk_id,
                {
                    "chunk_id": chunk_id,
                    "doc_id": row["doc_id"],
                    "text": row["text"],
                    "direct_terms": set(),
                    "expanded_terms": set(),
                },
            )
            merged[chunk_id]["expanded_terms"].update(row.get("hit_terms", []))

        # 2. 计算分数并构建 RetrievedChunk 列表
        scored_chunks: list[RetrievedChunk] = []

        for item in merged.values():
            direct_count = len(item["direct_terms"])
            expanded_count = len(item["expanded_terms"])

            score = (
                self.direct_hit_weight * direct_count
                + self.expanded_hit_weight * expanded_count
            )

            scored_chunks.append(
                RetrievedChunk(
                    chunk_id=item["chunk_id"],
                    doc_id=item["doc_id"],
                    text=item["text"],
                    score=score,
                    source="graph",
                )
            )

        scored_chunks.sort(key=lambda x: (-x.score, x.chunk_id))
        return scored_chunks[:top_k]



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


    def _expand_terms(self, direct_terms: list[str]) -> list[str]:
        '''
        包装事务调用, 并把Cypher结果拍平成最终expanded term list。
        '''

        if not direct_terms:
            return []
        with self.driver.session(database=self.database) as session:
            rows = session.execute_read(
                self._expand_terms_tx,
                {
                    "terms": direct_terms,
                    "per_term_limit": self.expand_per_term_limit,
                },
            )
        expanded_terms = []
        seen = set(direct_terms)

        for row in rows:
            for candidate in row.get("expanded", []):
                term = candidate["term"]
                if term in seen:
                    continue
                seen.add(term)
                expanded_terms.append(term)

                if len(expanded_terms) >= self.max_expanded_terms:
                    return expanded_terms
                
        return expanded_terms


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
    


from __future__ import annotations

from typing import Dict, List

from graph_rag.domain.models import RetrievedChunk
from graph_rag.domain.graph_models import ChunkGraphRecord, GraphNode, GraphEdge

from graph_rag.ports.graph_store import GraphStorePort

from graph_rag.common.text_utils import extract_terms

class InMemoryGraphStore(GraphStorePort):
    """
    Day 2: In-memory graph retrieval (substring matching)
    Day 3: Replace with Neo4j + Cypher

    Implements GraphStorePort:
    - upsert_document()
    - search() → RetrievedChunk(source="graph")

    Goal: enable vector + graph dual retrieval
    """

    def __init__(self) -> None:
        self.nodes_by_name = {}
        self.edges_by_pair = {}
        self.term_to_chunk_ids = {}
        self.chunk_terms = {}
        self.chunk_store = {}
        self.doc_to_chunk_ids = {}

    def upsert_chunk_graphs(self, records: List[ChunkGraphRecord]) -> None:
        for record in records:
            # record转成一个 RetrievedChunk 存起来：
            self.chunk_store[record.chunk_id] = RetrievedChunk(
                chunk_id=record.chunk_id,
                doc_id=record.doc_id,
                text=record.text,
                score=0.0,
                source="graph",
            )

            # 保存chunk terms
            terms = set(record.terms)  # 转变成集合
            self.chunk_terms[record.chunk_id] = terms

            # term -> chunk索引
            for term in terms:
                if term not in self.term_to_chunk_ids:
                    self.term_to_chunk_ids[term] = set()
                self.term_to_chunk_ids[term].add(record.chunk_id)
            
            # 建node
            for term in terms:
                if term not in self.nodes_by_name:
                    self.nodes_by_name[term] = GraphNode(
                        node_id=term,
                        name=term,
                        node_type="keyword",
                    )
            
            # 建edge
            sorted_terms = sorted(terms)
            for i in range(len(sorted_terms)):
                for j in range(i + 1, len(sorted_terms)):
                    a = sorted_terms[i]
                    b = sorted_terms[j]
                    key = (a, b)
                    if key not in self.edges_by_pair:
                        self.edges_by_pair[key] = GraphEdge(
                            edge_id=f"{a}__{b}",
                            source_node_id=a,
                            target_node_id=b,
                            edge_type="co_occurrence",
                            weight=1.0,
                        )
                    else:
                        old = self.edges_by_pair[key]
                        self.edges_by_pair[key] = GraphEdge(
                            edge_id=old.edge_id,
                            source_node_id=old.source_node_id,
                            target_node_id=old.target_node_id,
                            edge_type=old.edge_type,
                            weight=old.weight + 1.0,
                        )
            
        

    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        if not query:
            return []
        # 提query terms
        query_terms = extract_terms(query)
        if not query_terms:
            return []

        query_term_set = set(query_terms)

        # 找候选chunk，包含当前terms的chunk
        candidate_chunk_ids = set()
        for term in query_terms:
            candidate_chunk_ids.update(self.term_to_chunk_ids.get(term, set()))

        # 计算分数
        results: List[RetrievedChunk] = []

        for chunk_id in candidate_chunk_ids:
            # 找到每个候选chunk包含的term集合
            chunk_terms = self.chunk_terms.get(chunk_id, set())
            matched_terms = query_term_set & chunk_terms  # 命中 query 的 terms数目
            if not matched_terms:
                continue

            score = len(matched_terms) / max(1, len(query_term_set))
            chunk = self.chunk_store[chunk_id]
            
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    text=chunk.text,
                    score=score,
                    source="graph",
                )
            )
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
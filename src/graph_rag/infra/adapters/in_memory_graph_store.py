from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set

from graph_rag.domain.models import RetrievedChunk
from graph_rag.domain.graph_models import ChunkGraphRecord, GraphNode, GraphEdge
from graph_rag.ports.graph_store import GraphStorePort
from graph_rag.common.text_utils import extract_terms


class InMemoryGraphStore(GraphStorePort):
    """
    Implements GraphStorePort:
    - upsert_chunk_graphs()
    - search() -> RetrievedChunk(source="graph")

    Graph Retrieval V2:
    - direct term match
    - 1-hop term expansion
    - weighted scoring
    """

    def __init__(
            self,
            expand_per_term_limit: int = 2,
            direct_hit_weight: float = 1.0,
            expanded_hit_weight: float = 0.5,
            max_expanded_terms: int = 10,
            ) -> None:
        self.expand_per_term_limit = expand_per_term_limit
        self.direct_hit_weight = direct_hit_weight
        self.expanded_hit_weight = expanded_hit_weight
        self.max_expanded_terms = max_expanded_terms

        # chunk_id -> RetrievedChunk
        self.chunk_store: Dict[str, RetrievedChunk] = {}
        
        # term -> set(chunk_id)
        self.term_to_chunk_ids: Dict[str, Set[str]] = defaultdict(set)
        
        # term -> {neighbor_term: weight}
        self.term_graph: Dict[str, Dict[str, int]] = defaultdict(dict)


        # optional graph-like debug/state structures
        self.nodes_by_name: Dict[str, GraphNode] = {}
        self.edges_by_pair: Dict[tuple[str, str], GraphEdge] = {}
        self.chunk_terms: Dict[str, Set[str]] = {}
        self.doc_to_chunk_ids: Dict[str, Set[str]] = defaultdict(set)


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
            # record.terms优先；没有的话从text里抽
            raw_terms = record.terms if getattr(record, "terms", None) else extract_terms(record.text)
            terms = list(dict.fromkeys(raw_terms))  # 保序去重
            term_set = set(terms)

            self.chunk_terms[record.chunk_id] = term_set
            self.doc_to_chunk_ids[record.doc_id].add(record.chunk_id)

            self._index_chunk_terms(record, terms)
            self._update_term_cooccurrence(terms)


    def search(self, query: str, top_k: int) -> List[RetrievedChunk]:
        if not query:
            return []
        # 提query terms
        direct_terms  = extract_terms(query)
        if not direct_terms :
            return []
        
        expanded_terms = self._expand_terms(direct_terms)
        direct_hits = self._collect_chunk_hits(direct_terms)  # chunk_id -> 命中 term集合
        expanded_hits = self._collect_chunk_hits(expanded_terms)
        return self._build_retrieved_chunks(direct_hits, expanded_hits, top_k)

    
    def _index_chunk_terms(self, record: ChunkGraphRecord, terms: List[str]) -> None:
        # 这个函数的作用是把一个chunk的terms信息索引到self.term_to_chunk_ids里，
        # 以便后续检索时快速找到命中某个term的chunk_id集合。
        for term in terms:
            self.term_to_chunk_ids[term].add(record.chunk_id)

            # 建node
            if term not in self.nodes_by_name:
                self.nodes_by_name[term] = GraphNode(
                    node_id=term,
                    name=term,
                    node_type="keyword",
                )


    def _update_term_cooccurrence(self, terms: list[str]) -> None:
        # 这个函数的作用是根据一个chunk里terms的共现关系来更新self.term_graph和self.edges_by_pair，
        sorted_terms = sorted(set(terms))
        for i in range(len(sorted_terms)):
            for j in range(i + 1, len(sorted_terms)):
                a = sorted_terms[i]
                b = sorted_terms[j]

                # 1) 更新term_graph（search真正使用这个）
                self.term_graph[a][b] = self.term_graph[a].get(b, 0) + 1
                self.term_graph[b][a] = self.term_graph[b].get(a, 0) + 1

                # 2) 同步更新edges_by_pair（保留你原有图结构表示）
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


    def _expand_terms(self, direct_terms: list[str]) -> list[str]:
        '''遍历每个direct_term
        从self.term_graph[term]找到邻居term及权重
        按：权重降序 erm名字升序
        每个direct term截断前expand_per_term_limit
        排除原始direct terms
        全局去重
        最终总量不超过max_expanded_terms'''
        expanded: List[str] = []
        seen = set(direct_terms)

        for term in direct_terms:
            neighbors = self.term_graph.get(term, {})
            ranked = sorted(
                neighbors.items(),
                key=lambda x: (-x[1], x[0])
            )

            count = 0
            for neighbor_term, _weight in ranked:
                if neighbor_term in seen:
                    continue
                seen.add(neighbor_term)
                expanded.append(neighbor_term)
                count += 1
                if count >= self.expand_per_term_limit:
                    break
            
            if len(expanded) >= self.max_expanded_terms:
                break

        return expanded[: self.max_expanded_terms]

    
    def _collect_chunk_hits(self, terms: list[str]) -> dict[str, set[str]]:
        # 表示每个chunk命中了哪些distinct term 
        # return:
        #  hits = {
        # chunk_id: {"term1", "term2"},
        # "chunk2": {"apple", "banana"} 
        # }
        # 数据中：
        # self.term_to_chunk_ids = {
        #    "apple": {"chunk1", "chunk2"},
        #    "banana": {"chunk2"},
        #    "cat": {"chunk3"}
        #}
        hits: Dict[str, Set[str]] = {}
        for term in terms:
            for chunk_id in self.term_to_chunk_ids.get(term, set()):
                hits.setdefault(chunk_id, set()).add(term)
        return hits


    def _build_retrieved_chunks(
            self,
            direct_hits: dict[str, set[str]],
            expanded_hits: dict[str, set[str]],
            top_k: int,
        ) -> list[RetrievedChunk]:
        ''' 
        1. 取chunk_id并集
        2. 对每个chunk计算:
            direct_count = len(direct_hits.get(chunk_id, set()))
            expanded_count = len(expanded_hits.get(chunk_id, set()))
            score = direct_hit_weight * direct_count + expanded_hit_weight * expanded_count
        3. 从chunk_store取原始chunk内容
        4. 构造成RetrievedChunk(source="graph")
        5. 按: score DESC, chunk_id ASC
        6. 截断top_k
        '''
        chunk_ids = set(direct_hits.keys()) | set(expanded_hits.keys())
        scored_chunks: List[RetrievedChunk] = []
        
        for chunk_id in chunk_ids:
            direct_count = len(direct_hits.get(chunk_id, set()))  # chunk命中了多少个direct term
            expanded_count = len(expanded_hits.get(chunk_id, set()))  # chunk命中了多少个expanded term
            
            score = (
                self.direct_hit_weight * direct_count
                + self.expanded_hit_weight * expanded_count
                )  # 用chunk命中term的数量来打分，直接命中和扩展命中的权重不同

            chunk = self.chunk_store[chunk_id]
            scored_chunks.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    text=chunk.text,
                    score=score,
                    source="graph",
                )
            )
            
        scored_chunks.sort(key=lambda x: (-x.score, x.chunk_id))  # score范围是[0, inf)，score越大越相关；chunk_id升序保证同分时id小的在前面
        return scored_chunks[:top_k]
    
    
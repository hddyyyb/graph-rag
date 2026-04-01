from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from graph_rag.domain.models import RetrievedChunk
from graph_rag.domain.graph_models import ChunkGraphRecord, GraphNode, GraphEdge
from graph_rag.ports.graph_store import GraphStorePort
from graph_rag.common.text_utils import extract_terms


class InMemoryGraphStore(GraphStorePort):
    """
    Implements GraphStorePort:
    - upsert_chunk_graphs()
    - search() -> RetrievedChunk(source="graph")

    Graph Retrieval V2 / Day29:
    - direct term match
    - 1-hop term expansion
    - edge-weight-aware expanded term ranking
    - weighted scoring with explainable debug

    Day 29 基于图的权重的的检索与前面基于命中数量的检索的区别：
    检索时新增contribution的概念：每个命中的expanded term除了知道是哪个query term扩展来的、
    term本身是什么、权重是多少之外，还计算出它对最终score的贡献
    （contribution = weight * self.expanded_hit_weight），
    然后在计算chunk的总score时，不是简单地用命中数量乘以权重，
    而是直接把每个命中的expanded term的contribution加起来，
    这样就更细粒度地利用了图结构信息来影响检索结果的排序
    Why this change is necessary: 
    your current in-memory store already tracks co-occurrence frequency in term_graph, 
    but in search() it still flattens expanded terms to plain strings 
    and then scores only by expanded hit count, so edge weights never affect ranking yet.

    Scoring Mechanism (Graph Retrieval V2)

    1. Direct Term Scoring (精确命中)
    --------------------------------------------------
    - direct terms = query中直接抽取的关键词
    - 不使用图结构（无edge weight）
    - 只判断是否命中，不区分term重要性

    规则：
        每命中一个 distinct direct term，增加固定分值

    公式：
        direct_score = direct_hit_count * direct_hit_weight

    特点：
        - 所有direct term权重相同
        - 不考虑term之间的关系（不使用term_graph）
        - 是一个“纯倒排匹配 + 计数打分”的机制


    2. Expanded Term Scoring（图扩展命中）
    --------------------------------------------------
    - expanded terms = 基于term_graph的1-hop邻居扩展
    - 每个expanded term带有edge weight（共现强度）

    规则：
        每次命中一个expanded term，根据边权计算贡献值：

            contribution = edge_weight * expanded_hit_weight

    说明：
        - edge_weight来自term_graph（term之间的共现次数）
        - expanded_hit_weight是全局缩放系数

    chunk的expanded_score为所有命中贡献之和：

        expanded_score = sum(contribution_i)


    3. Final Score（最终排序分数）
    --------------------------------------------------
    最终分数由两部分组成：

        score = direct_score + expanded_score

    等价于：

        score = (direct_hit_count * direct_hit_weight)
            + sum(edge_weight * expanded_hit_weight)


    4. Example
    --------------------------------------------------
    query:
        direct_terms = ["transformer", "attention"]

    chunk命中情况：
        direct_hits = {"attention"}

        expanded_hits = [
            {"expanded_term": "encoder", "weight": 3.0, "contribution": 1.5},
            {"expanded_term": "softmax", "weight": 4.0, "contribution": 2.0},
        ]

    参数：
        direct_hit_weight = 1.0
        expanded_hit_weight = 0.5

    计算：
        direct_score   = 1 * 1.0 = 1.0
        expanded_score = 1.5 + 2.0 = 3.5

        total_score = 4.5


    5. Design Insight
    --------------------------------------------------
    - direct部分：保证“精确匹配”的基础相关性（recall稳定）
    - expanded部分：利用图结构进行语义扩展（ranking增强）
    - 两者结合：实现“精确 + 语义”的混合检索机制

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

        self._last_debug: Optional[Dict[str, Any]] = None
    

    def get_last_debug(self) -> Optional[Dict[str, Any]]:
        return self._last_debug
    

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
        self._last_debug = None

        if not query or top_k <= 0:
            self._last_debug = self._empty_debug_payload(query)
            return []

        direct_terms  = extract_terms(query)
        if not direct_terms :
            self._last_debug = self._empty_debug_payload(query)
            return []
        
        expanded_term_items = self._expand_terms_with_weights(direct_terms)

        direct_hits = self._collect_chunk_hits(direct_terms)  # chunk_id -> 命中 term集合
        
        expanded_hits = self._collect_chunk_weighted_hits(expanded_term_items)  # chunk_id -> 命中 expanded term的详细信息列表（包含是哪个query term扩展来的，expanded term是什么，权重是多少，以及对最终score的贡献）

        results = self._build_retrieved_chunks(
            direct_hits = direct_hits, 
            expanded_hits = expanded_hits, 
            top_k = top_k
            )
        
        self._last_debug = self._build_debug_payload(
            query=query,
            direct_terms=direct_terms,
            expanded_terms=expanded_term_items,
            direct_hits=direct_hits,
            expanded_hits=expanded_hits,
            results=results,
        )
        return results


    def _empty_debug_payload(self, query: str) -> Dict[str, Any]:
        return {
            "query": query,
            "direct_terms": [],
            "expanded_terms": [],
            "chunks": [],
            "weights": {
                "direct_hit_weight": self.direct_hit_weight,
                "expanded_hit_weight": self.expanded_hit_weight,
            },
            "scoring_formula": (
                "score = direct_hit_count * direct_hit_weight + "
                 "sum(expanded_edge_weight * expanded_hit_weight)",
            ),
            "meta": {
                "expansion_depth": 1,
                "expand_per_term_limit": self.expand_per_term_limit, 
                "max_expanded_terms": self.max_expanded_terms,
            },
        }
    

    '''expanded_terms = [
        {
            "query_term": "transformer",
            "expanded_term": "attention",
            "weight": 5.0
        },
        {
            "query_term": "attention",
            "expanded_term": "softmax",
            "weight": 4.0
        },
        {
            "query_term": "transformer",
            "expanded_term": "encoder",
            "weight": 3.0
        }
    ]
    
    expanded_hits = {
    "chunk_1": [
        {
        "query_term": "attention",
        "expanded_term": "softmax",
        "weight": 4.0,
        "contribution": 2.0
        }
    ],
    "chunk_2": [
        {
        "query_term": "transformer",
        "expanded_term": "encoder",
        "weight": 3.0,
        "contribution": 1.5
        },
        {
        "query_term": "attention",
        "expanded_term": "softmax",
        "weight": 4.0,
        "contribution": 2.0
        }
    ]
    }'''
    def _build_debug_payload(
        self,
        *,
        query: str,
        direct_terms: list[str],
        expanded_terms: list[dict[str, Any]],
        direct_hits: dict[str, set[str]],
        expanded_hits: dict[str, list[dict[str, Any]]],
        results: list[RetrievedChunk],
    ) -> dict[str, Any]:
        chunks_debug: list[dict[str, Any]] = []

        for chunk in results:
            direct_hit_terms = sorted(direct_hits.get(chunk.chunk_id, set()))
            expanded_hit_items = sorted(
                expanded_hits.get(chunk.chunk_id, []),
                key=lambda x: (-x["weight"], x["expanded_term"], x["query_term"]),
                )

            direct_score = len(direct_hit_terms) * self.direct_hit_weight
            expanded_score = sum(item["contribution"] for item in expanded_hit_items)
                                                                                    

            chunks_debug.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "direct_terms": direct_hit_terms,
                    "expanded_hits": expanded_hit_items,
                    "direct_hit_count": len(direct_hit_terms),
                    "expanded_hit_count": len(expanded_hit_items),
                    "direct_score": direct_score,
                    "expanded_score": expanded_score,
                    "score": chunk.score,
                }
            )

        return {
            "query": query,
            "direct_terms": sorted(direct_terms),
            "expanded_terms": expanded_terms,
            "chunks": chunks_debug,
            "weights": {
                "direct_hit_weight": self.direct_hit_weight,
                "expanded_hit_weight": self.expanded_hit_weight,
            },
            "scoring_formula": (
                "score = direct_hit_count * direct_hit_weight + "
                "sum(expanded_edge_weight * expanded_hit_weight)"
            ),
            "meta": {
                "expansion_depth": 1,
                "expand_per_term_limit": self.expand_per_term_limit,
                "max_expanded_terms": self.max_expanded_terms,
            },
        }


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

                # 1) 更新term_graph（邻接表+权重）
                # self.term_graph: Dict[str, Dict[str, int]] = defaultdict(dict)
                # 例如，self.term_graph的一个元素可能是：
                # { 
                #    "transformer": {"attention": 5, "encoder": 3},
                #    "attention": {"transformer": 5, "softmax": 4},
                #    ...
                # }
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


    def _expand_terms_with_weights(self, direct_terms: list[str]) -> list[dict[str, Any]]:
        '''遍历每个direct_term
        从self.term_graph[term]找到邻居term及权重
        按：权重降序 erm名字升序
        每个direct term截断前expand_per_term_limit
        排除原始direct terms
        全局去重
        最终总量不超过max_expanded_terms'''
        expanded: List[dict[str, Any]] = []
        seen = set(direct_terms)

        for term in direct_terms:
            neighbors = self.term_graph.get(term, {})
            ranked = sorted(
                neighbors.items(),
                key=lambda x: (-x[1], x[0])
            )

            count = 0
            for neighbor_term, weight in ranked:
                if neighbor_term in seen:
                    continue
                seen.add(neighbor_term)
                expanded.append(
                    {
                        "query_term": term,
                        "expanded_term": neighbor_term,
                        "weight": float(weight)
                    }
                )
                count += 1

                if count >= self.expand_per_term_limit:
                    break
            
            if len(expanded) >= self.max_expanded_terms:
                break
        
        expanded.sort(key=lambda x: (-x["weight"], x["expanded_term"], x["query_term"]))
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


    def _collect_chunk_weighted_hits(
            self, 
            expanded_terms: list[dict[str, Any]],
            ) -> dict[str, list[dict[str, Any]]]:
        hits: Dict[str, list[dict[str, Any]]] = defaultdict(list)
        
        for item in expanded_terms:
            expanded_term = item["expanded_term"]
            for chunk_id in self.term_to_chunk_ids.get(expanded_term, set()):
                contribution = float(item["weight"]) * self.expanded_hit_weight
                hits[chunk_id].append(
                    {   
                        "query_term": item["query_term"],
                        "expanded_term": expanded_term,
                        "weight": float(item["weight"]),
                        "contribution": contribution,
                    }  # weight comes from self.term_graph, is the edge weight between query_term and expanded_term
                )
        return hits  


    def _build_retrieved_chunks(
            self,
            direct_hits: dict[str, set[str]],
            expanded_hits: dict[str, list[dict[str, Any]]],
            top_k: int,
        ) -> list[RetrievedChunk]:
        ''' 
        1. 取chunk_id并集
        2. 对每个chunk计算:
            direct_count = len(direct_hits.get(chunk_id, set()))
            expanded_score = sum(item["contribution"] ...)
            score = self.direct_hit_weight * direct_count + expanded_score
        3. 从chunk_store取原始chunk内容
        4. 构造成RetrievedChunk(source="graph")
        5. 按: score DESC, chunk_id ASC
        6. 截断top_k
        '''
        chunk_ids = set(direct_hits.keys()) | set(expanded_hits.keys())
        scored_chunks: List[RetrievedChunk] = []
        
        for chunk_id in chunk_ids:
            direct_count = len(direct_hits.get(chunk_id, set()))  # chunk命中了多少个direct term
            expanded_score = sum(
                item["contribution"] for item in expanded_hits.get(chunk_id, []))  # 命中term contribution的和；expanded_hits：chunk_id: [{"query_term": "...", "expanded_term": "...", "weight": 4.0, "contribution": 2.0}]，对每个命中的expanded term，根据它的权重计算出对最终score的贡献，然后求和得到这个chunk的expanded_score
                       
            score = self.direct_hit_weight * direct_count + expanded_score  # 用chunk命中term的数量来打分，直接命中和扩展命中的权重不同
            # 到目前为止，后续的处理和基于命中数量无关，因此改为基于权重的方法时候，后面的代码不需要改或者改动很小
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
    
    
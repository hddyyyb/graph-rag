from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field

from graph_rag.domain.models import RetrievedChunk


# GraphExpandedTermDebug: 用于表示查询扩展的术语信息，包括原始查询术语、扩展术语和权重。
# “候选扩展空间”
class GraphExpandedTermDebug(BaseModel):  # Pydantic “声明式建模”
    query_term: str
    expanded_term: str
    weight: float


# GraphExpandedHitDebug: 用于表示查询扩展术语与文档块之间的匹配信息，包括查询术语、扩展术语、权重和贡献度。
class GraphExpandedHitDebug(BaseModel):
    query_term: str
    expanded_term: str
    weight: float
    contribution: float


# GraphChunkDebug: 用于表示查询结果中的文档块信息，包括块ID、文档ID、直接匹配术语、扩展匹配术语、直接匹配得分、扩展匹配得分和总得分。
# expanded_hits字段包含了每个扩展匹配术语对该文档块的贡献度信息，便于分析哪些扩展术语对最终得分影响最大。
# 命中了哪些词 -> 每个词贡献多少分
class GraphChunkDebug(BaseModel):
    chunk_id: str
    doc_id: str
    direct_terms: List[str] = Field(default_factory=list)
    expanded_hits: List[GraphExpandedHitDebug] = Field(default_factory=list)
    direct_hit_count: int = 0
    expanded_hit_count: int = 0
    direct_score: float = 0.0
    expanded_score: float = 0.0
    score: float = 0.0


# GraphSearchDebug: 用于表示整个查询过程的调试信息，包括原始查询、直接匹配术语、扩展匹配术语和查询结果中的文档块信息。
# expanded_terms字段包含了所有查询扩展术语的信息，chunks字段包含了所有查询结果中文档块的详细信息，便于分析查询扩展和匹配过程中的每个步骤。
# 系统级解释能力升级
class GraphSearchDebug(BaseModel):
    query: str = ""
    direct_terms: List[str] = Field(default_factory=list)
    expanded_terms: List[GraphExpandedTermDebug] = Field(default_factory=list)
    chunks: List[GraphChunkDebug] = Field(default_factory=list)
    weights: Dict[str, float] = Field(default_factory=dict)
    scoring_formula: str = ""
    meta:Dict[str, object] = Field(default_factory=dict)
    # object类型的meta字段可以用来存储任意额外的调试信息，例如查询时间、使用的算法版本等，这些信息对于后续分析和优化非常有帮助。


class GraphSearchResult(BaseModel):
    hits: List[RetrievedChunk] = Field(default_factory=list)
    debug: GraphSearchDebug = Field(default_factory=GraphSearchDebug)



'''
我们在 Graph Retrieval 中从 count-based scoring 升级为 weight-aware scoring，
并且设计了 fine-grained debug 结构，将每一个 expanded term 对 chunk 的贡献显式建模，
使得整个 graph scoring pipeline fully explainable and debuggable。'''
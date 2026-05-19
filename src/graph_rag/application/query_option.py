from __future__ import annotations
from typing import Optional
from pydantic import ValidationError

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryOptions:
    top_k: Optional[int] = None
    min_score: Optional[float] = None
    enable_vector: bool = True
    enable_graph: bool = True
'''
enable_vector, enable_graph语义不是 None → 使用默认
而是 
True  → 启用 vector retrieval
False → 禁用 vector retrieval
默认值 True 很合理。'''

def normalize_query_options(
        options: Optional[QueryOptions] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        enable_graph: Optional[bool] = None,
        enable_vector: Optional[bool] = None,
        ) -> QueryOptions:
    base = options or QueryOptions()
    
    normalized = QueryOptions(
        top_k=top_k if top_k is not None else base.top_k,
        min_score=min_score if min_score is not None else base.min_score,
        enable_graph=enable_graph if enable_graph is not None else base.enable_graph,
        enable_vector=enable_vector if enable_vector is not None else base.enable_vector,
    )
    
    if normalized.top_k is not None and normalized.top_k < 1:
        raise ValidationError("top_k must be greater than or equal to 1")

    if normalized.min_score is not None and normalized.min_score < 0:
        raise ValidationError("min_score must be greater than or equal to 0")

    if not normalized.enable_vector and not normalized.enable_graph:
        raise ValidationError("At least one retrieval mode must be enabled")

    return normalized
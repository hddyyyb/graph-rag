# models.py 放数据结构
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class EvalSample:
    query: str
    relevant_chunk_ids: List[str]

@dataclass
class EvalResult:
    mode: str
    query: str
    retrieved_chunk_ids: List[str]
    recall_at_k: float
    mrr: float
    relevant_chunk_ids: List[str]
    relevant_ranks: Dict[str, Optional[int]]
    false_negatives: List[str]
    false_positives: List[str]

@dataclass
class EvalSummary:
    mode: str
    k: int
    sample_count: int
    avg_recall_at_k: float
    avg_mrr: float
    
    
'''mode：当前评估模式，vector / graph / hybrid
query：本次查询
retrieved_chunk_ids：系统实际返回的chunk_id排序列表
recall_at_k：该query在K下的召回
mrr：该query的倒数排名'''
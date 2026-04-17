#metrics.py 放指标函数

def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    # Recall@K = 前K个结果中命中的相关chunk数 / 相关chunk总数
    if not relevant_ids:
        raise ValueError("relevant_ids cannot be empty")

    if k <= 0:
        raise ValueError("k must be positive")
    
    top_k = retrieved_ids[:k]
    hits = len(set(top_k) & set(relevant_ids))
    return hits / len(relevant_ids)


def mrr(retrieved_ids: list[str], relevant_ids: list[str]) -> float:
    # 第一个命中的相关结果排第几
    if not relevant_ids:
        raise ValueError("relevant_ids cannot be empty")

    for idx, chunk_id in enumerate(retrieved_ids):
        if chunk_id in relevant_ids:
            return 1.0 / (idx + 1)
    
    return 0.0
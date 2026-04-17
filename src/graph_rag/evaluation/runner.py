'''输入 sample.query
↓
调用 query_service
↓
拿到 retrieval 结果
↓
提取 chunk_id 列表
↓
调用 recall_at_k(...)
↓
调用 mrr(...)
↓
返回 EvalResult
'''
from graph_rag.evaluation.models import EvalSample, EvalResult, EvalSummary
from graph_rag.evaluation.metrics import recall_at_k, mrr

def _get_mode_flags(mode: str) -> tuple[bool, bool]:
    if mode == "hybrid":
        return True, True
    if mode == "vector":
        return True, False
    if mode == "graph":
        return False, True
    raise ValueError(f"unsupported evaluation mode: {mode}")


def evaluate_sample(
    sample: EvalSample, 
    query_service, 
    mode: str, 
    k:int
    )-> EvalResult:
    enable_vector, enable_graph = _get_mode_flags(mode)
    # 1. call existing retrieval pipeline
    result = query_service.query(
        query=sample.query, 
        top_k=k,
        enable_vector=enable_vector,
        enable_graph=enable_graph,
    )
    # 2. extract ranked chunk ids from citations
    # citations example:
    # [
    #     {"doc_id": "...", "chunk_id": "...", "source": "...", "score": ...}
    # ]
    citations = result.citations or []
    retrieved_chunk_ids = []

    for item in citations:
        chunk_id = item.get("chunk_id")
        if chunk_id is not None:
            retrieved_chunk_ids.append(chunk_id)
    
    # 3. compute metrics
    recall = recall_at_k(retrieved_chunk_ids, sample.relevant_chunk_ids, k)
    reciprocal_rank = mrr(retrieved_chunk_ids, sample.relevant_chunk_ids)
    
    # 4. build evaluation result
    return EvalResult(
        mode=mode,
        query=sample.query,
        retrieved_chunk_ids=retrieved_chunk_ids,
        recall_at_k=recall,
        mrr=reciprocal_rank,
    )
    
def evaluate_dataset(
    samples: list[EvalSample],
    query_service,
    mode: str,
    k: int,
) -> tuple[list[EvalResult], EvalSummary]:
    '''Evaluate a list of EvalSample objects and return a summary of the results'''
    if not samples:
        raise ValueError("samples cannot be empty")
    # 第一步：循环跑每个sample
    results = []
    for sample in samples:
        result = evaluate_sample(sample, query_service, mode=mode, k=k)
        results.append(result)

    avg_recall = sum(item.recall_at_k for item in results) / len(results)
    avg_mrr = sum(item.mrr for item in results) / len(results)
    '''EvalResult(
        mode="hybrid",
        query=sample.query,
        retrieved_chunk_ids=retrieved_chunk_ids,
        recall_at_k=recall,
        mrr=reciprocal_rank,
    )
    '''
    summary = EvalSummary(
        mode=mode,
        k=k,
        sample_count=len(samples),
        avg_recall_at_k=avg_recall,
        avg_mrr=avg_mrr,
    )

    return results,summary
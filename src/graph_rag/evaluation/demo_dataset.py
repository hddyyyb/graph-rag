from graph_rag.evaluation.models import EvalSample


DEMO_EVAL_SAMPLES = [
    EvalSample(
        query="python tutorial",
        relevant_chunk_ids=["chunk_1"],
    ),
    EvalSample(
        query="fastapi backend",
        relevant_chunk_ids=["chunk_2"],
    ),
    EvalSample(
        query="graph retrieval scoring",
        relevant_chunk_ids=["chunk_3"],
    ),
]
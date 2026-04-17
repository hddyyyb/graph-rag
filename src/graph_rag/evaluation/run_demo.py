from graph_rag.evaluation.demo_dataset import DEMO_EVAL_SAMPLES
from graph_rag.evaluation.runner import evaluate_dataset
from graph_rag.application.query_service import QueryService


def main():
    query_service = QueryService()  # 用你现有容器或测试服务构造方式拿到真实 QueryService

    for mode in ["vector", "graph", "hybrid"]:
        results, summary = evaluate_dataset(
            samples=DEMO_EVAL_SAMPLES,
            query_service=query_service,
            mode=mode,
            k=3,
        )

        print("=" * 60)
        print(f"mode: {summary.mode}")
        print(f"k: {summary.k}")
        print(f"sample_count: {summary.sample_count}")
        print(f"avg_recall_at_k: {summary.avg_recall_at_k:.4f}")
        print(f"avg_mrr: {summary.avg_mrr:.4f}")

        for item in results:
            print(
                f"[{item.mode}] query={item.query} "
                f"recall@{summary.k}={item.recall_at_k:.4f} "
                f"mrr={item.mrr:.4f} "
                f"retrieved={item.retrieved_chunk_ids}"
            )


if __name__ == "__main__":
    main()
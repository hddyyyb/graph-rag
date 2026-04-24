# Tests

## 目录结构

```
tests/
├── conftest.py                  # 全局 fixtures（FastAPI client、图存储实例、Neo4j 连接）
├── helpers.py                   # 测试工具函数
├── fakes/                       # 共享 Fake 实现
│   ├── fake_graph_store.py
│   └── fake_vector_store.py
│
├── application/                 # 业务逻辑单元测试
│   ├── test_ingest_service.py
│   ├── test_ingest_chunk_metadata.py
│   ├── test_ingest_file.py
│   ├── test_fuse_vector_graph.py
│   ├── test_query_service_graph_debug.py
│   └── test_query_service_*.py
│
├── infra/
│   ├── adapters/
│   │   ├── test_fixed_length_chunker.py
│   │   ├── test_recursive_chunker.py
│   │   └── test_sentence_transformer_embedding_provider.py
│   ├── graph/
│   │   ├── test_in_memory_graph_store.py
│   │   ├── test_inmemory_graph_store_debug.py
│   │   └── test_neo4j_graph_store.py
│   └── test_document_loader.py
│
├── api/                         # FastAPI 层测试
│   ├── test_create_app_settings.py
│   ├── test_query_graph_debug.py
│   └── test_graph_only_neo4j_closed_loop.py
│
├── integration/                 # 集成测试（依赖真实外部服务）
│   ├── test_real_sqlite_vector_retrieval.py
│   ├── test_graph_retrieval_closed_loop.py
│   ├── test_query_service_with_real_embedder.py
│   ├── test_graph_debug_consistency_between_memory_and_neo4j.py
│   └── test_container_neo4j_wiring.py
│
├── config/
│   └── test_settings.py
│
├── container/
│   └── test_build_container.py
│
├── evaluation/                  # 评估框架测试
│   ├── test_metrics.py
│   ├── test_runner.py
│   └── test_dataset_runner.py
│
└── test_*.py                    # 根级跨切面测试（见下方说明）
```

## 测试分类说明

### application/
针对 `IngestService` 和 `QueryService` 的单元测试，全部使用 Fake 依赖，不依赖真实存储或网络。

- `test_ingest_service.py` — 入库流程：切分、embedding、写向量库和图库
- `test_ingest_chunk_metadata.py` — 验证 chunk metadata 写入正确性
- `test_ingest_file.py` — 从文件路径入库的流程
- `test_fuse_vector_graph.py` — 向量检索与图检索的融合逻辑（`_fuse_chunks`）
- `test_query_service_graph_debug.py` — 查询时图调试信息的正确传递

### infra/
适配器层的单元测试，验证具体实现的行为。

- `test_fixed_length_chunker.py` / `test_recursive_chunker.py` — 切分策略
- `test_sentence_transformer_embedding_provider.py` — 本地 embedding 模型（需要模型文件）
- `test_in_memory_graph_store.py` / `test_neo4j_graph_store.py` — 图存储的 upsert 和 search

### api/
通过 `TestClient` 测试 HTTP 接口的请求/响应行为。

### integration/
依赖真实外部服务（SQLite 文件、Neo4j 数据库、真实 embedding 模型），通过 `pytest.skip` 在环境未配置时自动跳过。

### evaluation/
测试离线评估框架，包括 `recall@k`、`MRR` 指标计算和 `evaluate_dataset` 驱动逻辑。

### 根级 test_*.py（跨切面烟雾测试）

| 文件 | 测试内容 |
|------|----------|
| `test_services_smoke.py` | IngestService + QueryService 完整流程冒烟 |
| `test_clock_pluggable.py` | 时钟依赖可替换性 |
| `test_embedding_pluggable.py` | Embedding 适配器可替换性 |
| `test_vector_store_backend_switch.py` | SQLite / Milvus 后端切换 |
| `test_hybrid_vector_and_graph.py` | 混合检索端到端 |
| `test_vector_store_filter.py` | 向量检索 doc_id 过滤 |
| `test_filter_doc_id_day5.py` | 按 doc_id 过滤的细粒度场景 |
| `test_retrieval_post_processor.py` | 后处理器（top_k / min_score 截断） |
| `test_query_service_post_processor.py` | QueryService 集成后处理器 |
| `test_query_service_options.py` | QueryOptions 参数控制（enable_vector / enable_graph） |
| `test_simple_rag_kernel.py` | SimpleRAGKernel 生成逻辑 |
| `test_regroup.py` | chunk 重组逻辑 |
| `test_time_record.py` | 耗时记录字段 |
| `test_chunk_debug.py` | chunk 调试信息结构 |
| `test_failure.py` | 异常路径和错误处理 |
| `test_eval_real_benchmark.py` | 真实数据集基准评估（需要完整环境） |

## 运行方式

```bash
# 运行所有测试（跳过需要外部服务的集成测试）
pytest tests/ -v

# 只运行单元测试
pytest tests/application/ tests/infra/ -v

# 运行集成测试（需提前配置环境变量）
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=your_password
pytest tests/integration/ -v
```

## 主要 Fixtures（conftest.py）

| Fixture | 说明 |
|---------|------|
| `client` | FastAPI `TestClient` 实例 |
| `memory_store` | `InMemoryGraphStore`，每次测试独立实例 |
| `neo4j_store` | `Neo4jGraphStore`，依赖 `neo4j_driver` 和 `clean_graph` |
| `neo4j_driver` | 真实 Neo4j 驱动，测试结束后自动关闭 |
| `neo4j_config` | Neo4j 连接配置字典，从环境变量读取 |
| `clean_graph` | 测试前后自动清空 Neo4j 图数据库 |

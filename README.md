# GraphRAG工业级工程骨架

## 目标
一个可部署、可维护、可观测的GraphRAG服务骨架：双通道检索(向量+图)，Neo4j+Milvus存储，可插拔LLM，FastAPI服务化，Docker一键部署，支持增量更新。

## 快速开始(本地)
1) 创建虚拟环境并安装依赖
- python -m venv .venv
- source .venv/bin/activate
- pip install -e .

2) 启动依赖(Neo4j+Milvus)
- cp .env.example .env
- docker compose up -d

3) 启动API
- uvicorn graph_rag.api.main:app --reload --port 8000

4) 访问
- http://localhost:8000/docs

## API
- POST /ingest
- POST /query
- GET /health

## 架构
见docs/architecture.md

## 约束
- 不做算法优化
- 不调prompt
- 不关注模型效果
- 只关注系统架构与工程抽象
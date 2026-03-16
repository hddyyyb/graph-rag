# GraphRAG工业级工程冲刺计划目标(Day1版本)

## 项目一句话目标
构建一个企业级可部署的GraphRAG系统：支持向量检索+图检索双通道、Neo4j+Milvus存储、可插拔LLM、FastAPI服务化、Docker一键部署、支持增量更新，并能展示工程架构能力。

## 核心价值(工程视角)
- 可部署：DockerCompose一键拉起服务与依赖
- 可维护：分层清晰、接口稳定、可替换组件(LLM/向量库/图库/内核)
- 可观测：请求级trace_id、结构化日志、关键指标埋点
- 可扩展：新增数据源/检索策略/重排策略不改核心业务层
- 可测试：核心业务逻辑可在mock依赖下单测

## 明确不做(范围外)
- 不做算法优化(不改embedding算法、不做重排/召回调参)
- 不调prompt、不追求模型效果
- 不引入复杂编排(如K8s/HPA/ServiceMesh)作为Day1-30主线
- 不做多租户权限体系(可以预留接口，但不实现)

## Day30验收口径(方向性)
- 提供三个API：/ingest,/query,/health
- 支持增量更新：同doc_id重复入库可识别并更新
- 支持双通道检索：vector_only,graph_only,hybrid三种模式
- 可插拔：LLMProvider/VectorStore/GraphStore可替换
- 可观测：日志+trace_id+基础指标
- 可部署：DockerCompose+README能跑通demo

## Day1验收口径(今天)
- 输出目标与边界文档
- 输出需求文档
- 输出入库流与查询流文档
- 输出接口抽象文档
- 输出架构图(文字或png)
- 落地仓库骨架与README初版
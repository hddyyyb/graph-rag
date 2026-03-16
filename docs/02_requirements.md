# requirements

## 1.功能性需求
### 1.1数据入库
- 支持输入：本地文件(文本/markdown/pdf占位)、原始文本、URL占位
- 支持分块：默认按长度切分(先用LlamaIndex默认策略即可)
- 支持生成向量：通过EmbeddingProvider抽象
- 支持写入Milvus：以collection为隔离单元
- 支持写入Neo4j：至少包含Document/Chunk/Entity三类节点与关系
- 支持增量更新：以doc_id作为幂等键；重复入库时执行upsert语义
- 支持删除：按doc_id删除对应向量与图谱数据(可Day2-3实现)

### 1.2查询
- 提供查询模式：vector_only,graph_only,hybrid
- hybrid策略：并行召回->合并->交给内核生成回答(不做复杂重排)
- 返回结构：answer+citations+trace_id+timings+retrieval_debug

### 1.3管理与运维
- /health：连通性检查(服务存活+依赖可选检查)
- /metrics占位：先暴露关键计数与耗时(可先日志实现)

## 2.非功能性需求
- 可部署：DockerCompose启动(服务+Neo4j+Milvus)
- 可配置：环境变量覆盖本地配置，支持dev/prod配置文件
- 可观测：结构化日志(JSON)；每请求生成trace_id并贯穿调用链
- 可测试：业务层无外部依赖，单测可mock
- 可扩展：新增存储/LLM/内核不改业务层签名

## 3.约束
- 不做算法优化
- 不调prompt
- 不关注模型效果
- 只关注系统架构与工程抽象

## 4.不在范围(避免过度设计)
- 用户权限/鉴权/配额
- 多租户隔离
- 复杂任务编排与工作流引擎
- 全量可视化前端(可后续加一个简单Swagger或静态页)

## 5.关键定义
- doc_id：业务唯一标识，幂等键
- chunk_id：由doc_id+chunk_index生成
- trace_id：请求级追踪ID，贯穿日志与响应
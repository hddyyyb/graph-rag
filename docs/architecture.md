# architecture(文字版)

## 1.分层与依赖方向
[API层FastAPI]
  -> [Application层UseCases:IngestService/QueryService]
    -> [Domain层Entities+Errors+DTO]
      -> [Ports层Interfaces:VectorStore/GraphStore/EmbeddingProvider/Kernel/Observability]
        -> [Infra层Adapters:MilvusAdapter/Neo4jAdapter/LLMAdapter/LlamaIndexKernelAdapter]
          -> [External:Milvus,Neo4j,LLM]

依赖方向：API->Application->Domain->Ports
Infra实现Ports接口，Domain与Application禁止直接import具体数据库SDK。

## 2.运行时组件
- graph_rag_api:FastAPI服务(唯一对外入口)
- neo4j:图库
- milvus:向量库
- 可选：llm服务(本地或远程)

## 3.可插拔点(必须在Ports层)
- VectorStore:MilvusAdapter/FAISSAdapter(未来)
- GraphStore:Neo4jAdapter/ArangoAdapter(未来)
- EmbeddingProvider:OpenAI/LocalModel(未来)
- Kernel:LlamaIndexKernel/CustomKernel(未来)

## 4.数据模型最小集
- Neo4j:
  - (:Document{doc_id,...})-[:HAS_CHUNK]->(:Chunk{chunk_id,doc_id,index,...})
  - (:Chunk)-[:MENTIONS]->(:Entity{name,...})占位
- Milvus:
  - collection:chunks
  - primary_key:chunk_id
  - fields:vector,text,doc_id,metadata

## 5.部署形态
- docker-compose:
  - api容器
  - neo4j容器
  - milvus容器(含etcd/minio按官方compose)
- 配置通过.env注入，支持dev/prod切换
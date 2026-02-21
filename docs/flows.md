# flows

## 1.入库流(ingest)
### 1.1输入
- POST /ingest
- body:
  - doc_id:string
  - source_type: text|file|url
  - content:string(当source_type=text时必填)
  - metadata:object(可选)

### 1.2主流程
1) API层校验参数->生成trace_id
2) IngestService开始处理(记录start_time)
3) DocRepository检查doc_id是否存在
4) 分块Chunker: content->chunks
5) EmbeddingProvider: chunks->embeddings
6) VectorStore.upsert(chunks,embeddings,metadata)
7) GraphStore.upsert_document(doc_id,metadata)
8) GraphStore.upsert_chunks(doc_id,chunks)
9) GraphStore.link_doc_chunks(doc_id,chunk_ids)
10) 可选：EntityExtractor占位(先不做真实抽取)
11) 写入IngestLog(可用SQLite或文件占位)
12) 返回：ingest_id,doc_id,chunk_count,trace_id,timings

### 1.3幂等与增量更新策略
- 幂等键：doc_id
- upsert语义：
  - VectorStore按chunk_id覆盖写
  - GraphStore对Document/Chunk节点MERGE
- 若content_hash未变化：可直接短路返回(可Day2实现)

### 1.4失败分支与重试
- 外部依赖失败(Milvus/Neo4j):
  - 分类为可重试错误(Transient)
  - 返回HTTP503+error_code=DEPENDENCY_UNAVAILABLE
  - 日志记录trace_id+依赖名+异常栈
- 输入非法：
  - 返回HTTP400+error_code=INVALID_ARGUMENT
- 幂等冲突(如果你选择乐观锁)：
  - 返回HTTP409+error_code=CONFLICT

## 2.查询流(query)
### 2.1输入
- POST /query
- body:
  - query:string
  - mode: vector_only|graph_only|hybrid
  - top_k:int(默认8)
  - filters:object(可选，如doc_id范围)

### 2.2主流程
1) API层校验->生成trace_id
2) QueryService开始计时
3) 根据mode执行召回：
  - vector_only: VectorRetriever.search(query)->chunks
  - graph_only: GraphRetriever.search(query)->chunks
  - hybrid: 并行执行两路召回->合并去重->截断top_k
4) Kernel(基于LlamaIndex的QueryEngine封装)：
  - 输入：query+chunks上下文
  - 输出：answer+citations(引用chunk_id)
5) 组装响应：trace_id+timings+retrieval_debug
6) 返回HTTP200

### 2.3失败分支
- LLM不可用：
  - 返回HTTP503+error_code=LLM_UNAVAILABLE
  - 仍返回retrieval_debug便于排障
- 无结果：
  - answer给出“未检索到相关内容”(不要追求效果)
  - citations为空
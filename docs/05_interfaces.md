# interfaces

## 0.设计原则
- 业务层只依赖抽象(Protocol/ABC)，不依赖Neo4j/Milvus/LlamaIndex具体实现
- 接口以业务动作命名：ingest/query/update/delete
- 所有方法入参必须携带trace_id(或通过Context注入)
- 错误必须分类：InvalidArgument/Transient/Unavailable/Conflict/Internal

## 1.CoreDomain数据结构(建议)
- Document{doc_id,content,metadata,content_hash}
- Chunk{chunk_id,doc_id,text,index,metadata}
- RetrievalResult{chunks,debug}
- Answer{answer,citations,trace_id,timings}

## 2.接口清单(<=8)

### 2.1ConfigProvider
- get()->AppConfig

### 2.2EmbeddingProvider
- embed_texts(texts:list[str],trace_id:str)->list[list[float]]

### 2.3VectorStore
- upsert(chunks:list[Chunk],vectors:list[list[float]],trace_id:str)->None
- delete_by_doc(doc_id:str,trace_id:str)->None
- search(query:str,top_k:int,filters:dict,trace_id:str)->RetrievalResult

### 2.4GraphStore
- upsert_document(doc:Document,trace_id:str)->None
- upsert_chunks(chunks:list[Chunk],trace_id:str)->None
- link_doc_chunks(doc_id:str,chunk_ids:list[str],trace_id:str)->None
- delete_by_doc(doc_id:str,trace_id:str)->None
- search(query:str,top_k:int,filters:dict,trace_id:str)->RetrievalResult

### 2.5Kernel(内核封装，隐藏LlamaIndex)
- answer(query:str,chunks:list[Chunk],trace_id:str)->Answer

### 2.6IngestService(业务用例)
- ingest(doc:Document,trace_id:str)->dict(ingest_id,chunk_count,timings)

### 2.7QueryService(业务用例)
- query(query:str,mode:str,top_k:int,filters:dict,trace_id:str)->Answer

### 2.8Observability
- new_trace_id()->str
- log(event:dict)->None
- timer(name:str)->context_manager
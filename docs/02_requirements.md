# System Requirements

## Functional Requirements

### Data Ingestion

The system must support:

- text input
- file input
- URL input (placeholder)

Processing steps:

1 Document chunking
2 Embedding generation
3 Vector indexing
4 Graph indexing

The system must support incremental updates using `doc_id`.

### Query

The system must support three query modes:

- vector_only
- graph_only
- hybrid

Query result format:

answer
citations
trace_id
timings
retrieval_debug


### Management

The system provides:

/health endpoint  
/metrics placeholder

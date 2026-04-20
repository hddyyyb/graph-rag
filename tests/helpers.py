from __future__ import annotations

from typing import Optional

from graph_rag.application.query_service import QueryService
from graph_rag.infra.adapters import (
    DefaultRetrievalPostProcessor,
    FakeEmbeddingV2,
    SentenceTransformerEmbeddingProvider,
    FakeKernel,
    SimpleKernel,
    SimpleRAGKernel,
    InMemoryGraphStore,
    Neo4jGraphStore,
    InMemoryVectorStore,
    SQLiteVectorStore,
    FixedLengthChunker,
    RecursiveChunker,
    FixedClock,
    SystemClock,
    FakeLLM,
    LocalLLM,
    OpenAILLM,
)


from graph_rag.ports.document_loader import DocumentLoaderPort
from graph_rag.infra.document_loaders.simple_document_loader import SimpleDocumentLoader

from graph_rag.infra.observability.fake_trace import FakeTrace

from graph_rag.ports.vector_store import VectorStorePort
from graph_rag.ports.graph_store import GraphStorePort
from graph_rag.ports.embedding import EmbeddingProviderPort
from graph_rag.ports.kernel import RAGKernelPort
from graph_rag.ports.retrieval_post_processor import RetrievalPostProcessorPort
from graph_rag.ports.observability import TracePort
from graph_rag.ports.chunker import ChunkerPort

from tests.fakes.fake_vector_store import FakeVectorStore
from tests.fakes.fake_graph_store import FakeGraphStore

from graph_rag.application.ingest_service import IngestService


def build_test_service(
    *,
    vector_store: Optional[VectorStorePort] = None,
    graph_store: Optional[GraphStorePort] = None,
    embedder: Optional[EmbeddingProviderPort] = None,
    kernel: Optional[RAGKernelPort] = None,
    post_processor: Optional[RetrievalPostProcessorPort] = None,
    trace: Optional[TracePort] = None,
    vector_top_k: int = 5,
    graph_top_k: int = 5,
) -> QueryService:
    return QueryService(
        vector_store=vector_store or FakeVectorStore(),
        graph_store=graph_store or FakeGraphStore(),
        embedder=embedder or FakeEmbeddingV2(),
        kernel=kernel or FakeKernel(),
        post_processor=post_processor or DefaultRetrievalPostProcessor(),
        trace=trace or FakeTrace(),
        vector_top_k=vector_top_k,
        graph_top_k=graph_top_k,
    )

def build_basic_query_service(
    *,
    vector_store: Optional[VectorStorePort] = None,
    graph_store: Optional[GraphStorePort] = None,
    embedder: Optional[EmbeddingProviderPort] = None,
    kernel: Optional[RAGKernelPort] = None,
    post_processor: Optional[RetrievalPostProcessorPort] = None,
    trace: Optional[TracePort] = None,
    vector_top_k: int = 5,
    graph_top_k: int = 5,
) -> QueryService:
    return QueryService(
        vector_store=vector_store or InMemoryVectorStore(),
        graph_store=graph_store or InMemoryGraphStore(),
        embedder=embedder or SentenceTransformerEmbeddingProvider(),
        kernel=kernel or SimpleKernel(),
        post_processor=post_processor or DefaultRetrievalPostProcessor(),
        trace=trace or FakeTrace(),
        vector_top_k=vector_top_k,
        graph_top_k=graph_top_k,
    )

def build_test_ingest_service(
    *,
    vector_store: Optional[VectorStorePort] = None,
    graph_store: Optional[GraphStorePort] = None,
    embedder: Optional[EmbeddingProviderPort] = None,
    trace: Optional[TracePort] = None,
    chunker: Optional[ChunkerPort] = None,
    document_loader: Optional[DocumentLoaderPort] = None,
) -> IngestService:
    service = IngestService(
        vector_store= vector_store or InMemoryVectorStore(),
        graph_store= graph_store or InMemoryGraphStore(),
        embedder=embedder or FakeEmbeddingV2(),
        trace=trace or FakeTrace(),
        chunker=chunker or FixedLengthChunker(chunk_size=50, chunk_overlap=0),
        document_loader=document_loader or SimpleDocumentLoader(),
    )
    return service

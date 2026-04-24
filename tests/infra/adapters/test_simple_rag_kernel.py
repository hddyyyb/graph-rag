from graph_rag.domain.models import RetrievedChunk
from graph_rag.infra.adapters.fake_llm import FakeLLM
from graph_rag.infra.adapters.simple_rag_kernel import SimpleRAGKernel



def test_simple_rag_kernel_calls_llm_and_returns_reply():
    llm = FakeLLM(reply="ok")
    kernel = SimpleRAGKernel(llm=llm)

    contexts = [
        RetrievedChunk(
            doc_id="doc1",
            chunk_id="doc1#0",
            text="hello world",
            score=0.9,
            source="test",
        )
    ]


    out = kernel.generate_answer("what is this", contexts)

    assert out == "ok"
    assert "what is this" in llm.last_prompt
    assert "hello world" in llm.last_prompt

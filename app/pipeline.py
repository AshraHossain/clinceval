import time
from app.retriever import retrieve
from app.generator import generate

def run_pipeline(query: str, k: int = 3) -> dict:
    """
    Executes the full pipeline:
    1. Retrieves top k chunks from ChromaDB
    2. Invokes generator with context to get structured response
    3. Runs citation validation checks
    4. Packages final results
    """
    start_time = time.time()
    
    # 1. Retrieval
    chunks = retrieve(query, k=k)
    retrieved_ids = {chunk["id"] for chunk in chunks}
    
    # 2. Generation
    gen_result = generate(query, chunks)
    
    # 3. Citation Check
    citations = gen_result.get("citations", [])
    invalid_citations = [cit for cit in citations if cit not in retrieved_ids]
    citations_valid = len(invalid_citations) == 0
    
    total_time = time.time() - start_time
    
    return {
        "query": query,
        "retrieved_chunks": chunks,
        "recommendation": {
            "calculator": gen_result.get("calculator"),
            "rationale": gen_result.get("rationale"),
            "confidence": gen_result.get("confidence"),
            "citations": citations
        },
        "citations_valid": citations_valid,
        "invalid_citations": invalid_citations,
        "metrics": {
            "retrieval_count": len(chunks),
            "generation_latency": gen_result.get("latency"),
            "pipeline_latency": total_time,
            "input_tokens": gen_result.get("input_tokens"),
            "output_tokens": gen_result.get("output_tokens")
        }
    }

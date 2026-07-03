import json
from app.llm import get_llm_client

GENERATOR_MODEL = "claude-3-5-haiku-20241022"

RECOMMEND_TOOL = {
    "name": "recommend_calculator",
    "description": "Provide a recommendation for a medical calculator based on patient symptoms.",
    "input_schema": {
        "type": "object",
        "properties": {
            "calculator": {
                "type": "string",
                "description": "Name of the recommended calculator, e.g., 'CHA2DS2-VASc', 'Wells PE', 'MELD', 'CURB-65', 'HEART Score', 'Glasgow Coma Scale', or 'None' if no clinical calculator matches."
            },
            "rationale": {
                "type": "string",
                "description": "Reasoning for why the calculator is recommended or why 'None' is chosen. Cite specific patient symptoms and findings from the query."
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score from 0.0 to 1.0."
            },
            "citations": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of chunk IDs from the provided context that directly support this recommendation."
            }
        },
        "required": ["calculator", "rationale", "confidence", "citations"]
    }
}

SYSTEM_PROMPT = """You are a mock clinical assistant that recommends medical calculators based on patient symptoms.
Your job is to recommend the single most appropriate medical calculator from the provided context.

Rules:
1. ONLY recommend calculators that are explicitly described in the provided context. If no calculator matches, return "None" as the calculator and explain why in the rationale.
2. Rely strictly on facts from the context. Do not make up scoring systems, criteria, or calculators.
3. In your citations, specify the exact chunk IDs from the context that you used.
4. You must call the `recommend_calculator` tool to output your recommendation.
"""

def generate(query: str, retrieved_chunks: list[dict]) -> dict:
    """
    Format retrieved context, call Claude, and return the structured recommendation.
    """
    # Format retrieved context
    context_str = ""
    for chunk in retrieved_chunks:
        context_str += f"--- START CHUNK ID: {chunk['id']} ---\n"
        context_str += f"{chunk['text']}\n"
        context_str += f"--- END CHUNK ID: {chunk['id']} ---\n\n"
        
    user_prompt = f"Patient Query:\n{query}\n\nRetrieved Context:\n{context_str}"
    
    llm_client = get_llm_client()
    result = llm_client.call_claude(
        model=GENERATOR_MODEL,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tools=[RECOMMEND_TOOL],
        tool_choice={"type": "tool", "name": "recommend_calculator"}
    )
    
    # Extract tool input
    response = result["response"]
    tool_use = next(block for block in response.content if block.type == "tool_use")
    structured_data = tool_use.input
    
    # Return structured data combined with usage metadata
    return {
        "calculator": structured_data.get("calculator"),
        "rationale": structured_data.get("rationale"),
        "confidence": structured_data.get("confidence"),
        "citations": structured_data.get("citations", []),
        "latency": result["latency"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"]
    }

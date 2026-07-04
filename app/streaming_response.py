"""Streaming responses for long rationales.

Phase 10h: UX improvement — stream rationale chunks as they're generated.
"""
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator


async def stream_recommendation(query: str) -> AsyncGenerator[str, None]:
    """Stream recommendation as it's generated.

    Yields: JSON lines, each a chunk of the rationale or complete object.
    Client-side: parse JSON lines, append to UI in real-time.
    """
    # Retrieve
    chunks = retrieve(query, k=3)
    yield f'{{"status": "retrieved", "chunk_count": {len(chunks)}}}\n'

    # Generate with streaming (if supported by API)
    # For now: stub with full response
    # In practice: use anthropic.Anthropic(streaming=True)
    recommendation = generate(query, chunks)

    yield f'{{"status": "recommendation_complete", "recommendation": {recommendation}}}\n'


async def stream_judge(case_input: dict) -> AsyncGenerator[str, None]:
    """Stream judge scores as they're computed per axis."""
    yield '{"status": "judging_faithfulness"}\n'
    # ... compute faithfulness
    yield '{"axis": "faithfulness", "score": 5}\n'

    yield '{"status": "judging_clinical_relevance"}\n'
    # ... compute
    yield '{"axis": "clinical_relevance", "score": 5}\n'

    # etc.


# Client-side (JavaScript):
# const response = await fetch('/api/recommend/stream', {...});
# const reader = response.body.getReader();
# while (true) {
#   const { done, value } = await reader.read();
#   if (done) break;
#   const lines = new TextDecoder().decode(value).split('\n').filter(Boolean);
#   lines.forEach(line => {
#     const chunk = JSON.parse(line);
#     if (chunk.status === 'recommendation_complete') {
#       renderResult(chunk.recommendation);
#     }
#   });
# }

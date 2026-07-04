"""Per-run latency, token, and cost accounting for all LLM calls.

Every call funnels through LLMClient.call_claude (project convention), which
records here. The regression runner snapshots the accumulated events into its
report, then resets for the next run.
"""
from dataclasses import dataclass

# USD per million tokens (input, output) for the pinned models
PRICES_PER_MTOK = {
    "claude-3-5-haiku-20241022": (0.80, 4.00),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
}


@dataclass
class CallEvent:
    model: str
    latency: float
    input_tokens: int
    output_tokens: int
    mock: bool


_events: list[CallEvent] = []


def record(model: str, latency: float, input_tokens: int, output_tokens: int, mock: bool) -> None:
    _events.append(CallEvent(model, latency, input_tokens, output_tokens, mock))


def estimate_cost(event: CallEvent) -> float:
    if event.mock:
        return 0.0
    price_in, price_out = PRICES_PER_MTOK.get(event.model, (0.0, 0.0))
    return (event.input_tokens * price_in + event.output_tokens * price_out) / 1_000_000


def snapshot_and_reset() -> dict:
    """Aggregate accumulated events and clear the buffer."""
    global _events
    events, _events = _events, []
    total_latency = sum(e.latency for e in events)
    return {
        "calls": len(events),
        "mock_calls": sum(1 for e in events if e.mock),
        "total_latency_s": round(total_latency, 3),
        "avg_latency_s": round(total_latency / len(events), 3) if events else 0.0,
        "input_tokens": sum(e.input_tokens for e in events),
        "output_tokens": sum(e.output_tokens for e in events),
        "estimated_cost_usd": round(sum(estimate_cost(e) for e in events), 4),
    }

from __future__ import annotations

import re

KNOWLEDGE_TERMS = [
    "implementation shortfall", "vwap", "liquidity", "execution risk",
    "bid-ask", "bid ask", "market impact", "arrival price", "execution cost",
    "benchmark", "spread"
]


def _top_n(question: str, default: int = 5) -> int:
    match = re.search(r"\b(?:top|worst|largest|highest)\s+(\d+)\b", question.lower())
    if match:
        return max(1, min(int(match.group(1)), 25))
    return default


def route_question(question: str) -> dict:
    q = question.lower().strip()

    trade_match = re.search(r"\btrd\d{4}\b", q)
    if trade_match:
        return {"route": "data", "tool": "lookup_trade", "args": {"trade_id": trade_match.group(0).upper()}}

    if any(term in q for term in ["data quality", "quality issue", "invalid record", "duplicate", "missing benchmark"]):
        return {"route": "data", "tool": "data_quality", "args": {}}

    if any(term in q for term in ["partial fill", "fill rate", "not fully filled", "unfilled"]):
        return {"route": "data", "tool": "partial_fills", "args": {"n": _top_n(q, 10)}}

    if "venue" in q and any(term in q for term in ["slippage", "execution", "worst", "best", "compare", "average", "mean"]):
        return {"route": "data", "tool": "venue_summary", "args": {}}

    if "asset class" in q and any(term in q for term in ["slippage", "execution", "worst", "best", "compare", "average", "mean"]):
        return {"route": "data", "tool": "asset_class_summary", "args": {}}

    if any(term in q for term in ["worst execution", "highest slippage", "largest slippage", "largest deviation", "worst trades"]):
        return {"route": "data", "tool": "worst_executions", "args": {"n": _top_n(q, 10)}}

    if any(term in q for term in KNOWLEDGE_TERMS):
        return {"route": "knowledge", "tool": "rag", "args": {}}

    return {"route": "unsupported", "tool": "scope_guard", "args": {}}

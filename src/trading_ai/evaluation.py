from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from .analytics import load_trades
from .config import REFUSAL_TEXT
from .rag import TradingRAG
from .router import route_question


ROUTER_CASES = [
    ("What is implementation shortfall?", "knowledge"),
    ("Why can liquidity affect execution quality?", "knowledge"),
    ("What does VWAP mean?", "knowledge"),
    ("Which venue has the worst average execution slippage?", "data"),
    ("Show the top 5 worst executions", "data"),
    ("Show partial fills", "data"),
    ("What data quality issues are present?", "data"),
    ("Compare execution by asset class", "data"),
    ("Show TRD0010", "data"),
    ("How do I make pizza?", "unsupported"),
    ("What problem does MCP solve?", "unsupported"),
]

RAG_CASES = [
    ("What is implementation shortfall?", "execution_cost_notes.txt"),
    ("Why can liquidity affect execution quality?", "liquidity_notes.txt"),
    ("What factors can affect execution risk?", "execution_risk_notes.txt"),
    ("Why might a large trade be difficult to execute at one price?", "liquidity_notes.txt"),
]


def evaluate_router() -> pd.DataFrame:
    rows = []
    for question, expected in ROUTER_CASES:
        actual = route_question(question)["route"]
        rows.append({"question": question, "expected": expected, "actual": actual, "pass": actual == expected})
    return pd.DataFrame(rows)


def evaluate_data_quality() -> pd.DataFrame:
    df = load_trades()
    checks = {
        "duplicate_trade_id_rows_detected": int(df["flag_duplicate_trade_id"].sum()) >= 2,
        "missing_arrival_detected": int(df["flag_missing_arrival_price"].sum()) >= 1,
        "missing_vwap_detected": int(df["flag_missing_vwap_price"].sum()) >= 1,
        "invalid_quantity_detected": int(df["flag_invalid_quantity"].sum()) >= 1,
        "dirty_side_detected": int(df["flag_dirty_side"].sum()) >= 1,
        "extreme_slippage_detected": int(df["flag_extreme_arrival_slippage"].sum()) >= 1,
        "low_fill_detected": int(df["flag_low_fill"].sum()) >= 1,
    }
    return pd.DataFrame([{"check": k, "pass": bool(v)} for k, v in checks.items()])


def evaluate_rag_retrieval(top_k: int = 3) -> pd.DataFrame:
    rag = TradingRAG()
    rows = []
    for question, expected_source in RAG_CASES:
        results = rag.retrieve(question, top_k=top_k)
        sources = [r.source for r in results]
        rows.append({
            "question": question,
            "expected_source": expected_source,
            "retrieved_sources": " | ".join(sources),
            "hit_at_k": expected_source in sources,
            "top_score": results[0].score,
        })
    return pd.DataFrame(rows)


def evaluate_refusal() -> dict:
    rag = TradingRAG()
    result = rag.answer("What problem does MCP solve?")
    return {
        "question": result["question"],
        "answer": result["answer"],
        "exact_refusal": result["answer"].strip() == REFUSAL_TEXT,
    }

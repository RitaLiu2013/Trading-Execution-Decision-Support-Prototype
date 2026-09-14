from __future__ import annotations

import pandas as pd

from .analytics import (
    find_partial_fills,
    get_data_quality_summary,
    get_worst_executions,
    load_trades,
    lookup_trade,
    summarize_by_asset_class,
    summarize_by_venue,
)
from .llm import explain_tool_result
from .rag import TradingRAG
from .router import route_question

UNSUPPORTED_TEXT = (
    "This prototype supports trading-execution knowledge questions and analysis of the included synthetic execution dataset."
)


class TradingAssistant:
    def __init__(self, use_llm_explanations: bool = True):
        self.df = load_trades()
        self.use_llm_explanations = use_llm_explanations
        self._rag = None

    @property
    def rag(self) -> TradingRAG:
        if self._rag is None:
            self._rag = TradingRAG()
        return self._rag

    @staticmethod
    def _frame_to_text(frame: pd.DataFrame) -> str:
        if frame.empty:
            return "No rows matched the request."
        return frame.to_markdown(index=False, floatfmt=".4f")

    def _run_data_tool(self, tool: str, args: dict) -> pd.DataFrame:
        if tool == "data_quality":
            return get_data_quality_summary(self.df)
        if tool == "partial_fills":
            return find_partial_fills(self.df, n=args.get("n", 10))
        if tool == "venue_summary":
            return summarize_by_venue(self.df)
        if tool == "asset_class_summary":
            return summarize_by_asset_class(self.df)
        if tool == "worst_executions":
            return get_worst_executions(self.df, n=args.get("n", 10))
        if tool == "lookup_trade":
            return lookup_trade(self.df, args["trade_id"])
        raise ValueError(f"Unknown tool: {tool}")

    def answer(self, question: str) -> dict:
        route = route_question(question)

        if route["route"] == "unsupported":
            return {"question": question, "route": route, "answer": UNSUPPORTED_TEXT}

        if route["route"] == "knowledge":
            result = self.rag.answer(question)
            result["route"] = route
            return result

        frame = self._run_data_tool(route["tool"], route["args"])
        evidence = self._frame_to_text(frame)
        explanation = explain_tool_result(question, evidence) if self.use_llm_explanations else None
        return {
            "question": question,
            "route": route,
            "answer": explanation or evidence,
            "tool_output": evidence,
        }

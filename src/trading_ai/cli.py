from __future__ import annotations

import argparse

from .analytics import load_trades
from .evaluation import evaluate_data_quality, evaluate_router
from .synthetic_data import generate_synthetic_trades
from .workflow import TradingAssistant


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading Execution Decision-Support Prototype")
    parser.add_argument("--question", "-q", type=str, help="Ask one question")
    parser.add_argument("--no-llm", action="store_true", help="Do not use LLM explanations for data-tool outputs")
    parser.add_argument("--regenerate-data", action="store_true", help="Regenerate the synthetic CSV")
    parser.add_argument("--evaluate", action="store_true", help="Run fast deterministic evaluations")
    args = parser.parse_args()

    if args.regenerate_data:
        generate_synthetic_trades()
        print("Synthetic dataset regenerated.")

    if args.evaluate:
        print("\nRouter evaluation")
        print(evaluate_router().to_string(index=False))
        print("\nData-quality evaluation")
        print(evaluate_data_quality().to_string(index=False))
        return

    assistant = TradingAssistant(use_llm_explanations=not args.no_llm)
    question = args.question or input("Question: ").strip()
    result = assistant.answer(question)
    print(f"\nRoute: {result['route']['route']} / {result['route'].get('tool')}")
    print("\nAnswer:\n")
    print(result["answer"])
    if "tool_output" in result and result["answer"] != result["tool_output"]:
        print("\nDeterministic tool output:\n")
        print(result["tool_output"])


if __name__ == "__main__":
    main()

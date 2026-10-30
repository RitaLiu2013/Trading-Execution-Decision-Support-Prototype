from __future__ import annotations

import argparse
import json

from .evaluation import (
    evaluate_data_quality,
    evaluate_router,
)
from .governance_ai import run_governance_ai
from .synthetic_data import (
    generate_synthetic_trades,
)
from .workflow import TradingAssistant


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Trading Execution "
            "Decision-Support Prototype"
        )
    )

    parser.add_argument(
        "--question",
        "-q",
        type=str,
        help="Ask one question",
    )

    parser.add_argument(
        "--no-llm",
        action="store_true",
        help=(
            "Do not use LLM explanations "
            "for data-tool outputs"
        ),
    )

    parser.add_argument(
        "--regenerate-data",
        action="store_true",
        help="Regenerate the synthetic CSV",
    )

    parser.add_argument(
        "--evaluate",
        action="store_true",
        help=(
            "Run fast deterministic evaluations"
        ),
    )

    parser.add_argument(
        "--governance-ai",
        action="store_true",
        help=(
            "Run the AI-assisted governance "
            "drafting workflow"
        ),
    )

    parser.add_argument(
        "--issue-id",
        type=str,
        default="DQ-001",
        help=(
            "Governance issue ID used with "
            "--governance-ai"
        ),
    )

    args = parser.parse_args()

    if args.regenerate_data:
        generate_synthetic_trades()
        print(
            "Synthetic dataset regenerated."
        )

    if args.evaluate:
        print("\nRouter evaluation")

        print(
            evaluate_router().to_string(
                index=False
            )
        )

        print("\nData-quality evaluation")

        print(
            evaluate_data_quality().to_string(
                index=False
            )
        )

        return

    if args.governance_ai:
        result = run_governance_ai(
            issue_id=args.issue_id
        )

        print(
            f"\nGovernance issue: "
            f"{result['issue_id']}"
        )

        print(
            f"Accepted: "
            f"{result['accepted']}"
        )

        print(
            "\nValidation:"
        )

        print(
            json.dumps(
                result["validation"],
                indent=2,
            )
        )

        if result["draft"] is not None:
            print(
                "\nAI-generated draft:"
            )

            print(
                json.dumps(
                    result["draft"],
                    indent=2,
                    ensure_ascii=False,
                )
            )

        print(
            "\nDeterministic remediation action:"
        )

        print(
            result["evidence"][
                "remediation_action"
            ]
        )

        return

    assistant = TradingAssistant(
        use_llm_explanations=not args.no_llm
    )

    question = (
        args.question
        or input("Question: ").strip()
    )

    result = assistant.answer(question)

    print(
        f"\nRoute: "
        f"{result['route']['route']} / "
        f"{result['route'].get('tool')}"
    )

    print("\nAnswer:\n")
    print(result["answer"])

    if (
        "tool_output" in result
        and result["answer"]
        != result["tool_output"]
    ):
        print(
            "\nDeterministic tool output:\n"
        )

        print(result["tool_output"])


if __name__ == "__main__":
    main()
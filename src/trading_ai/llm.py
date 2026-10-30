from __future__ import annotations

import json

from .config import OLLAMA_MODEL_NAME, REFUSAL_TEXT


def _chat(
    messages: list[dict],
    model: str = OLLAMA_MODEL_NAME,
) -> str | None:
    try:
        from ollama import chat

        response = chat(
            model=model,
            messages=messages,
            options={"temperature": 0},
        )

        return response.message.content.strip()

    except Exception:
        return None


def _chat_structured(
    messages: list[dict],
    schema: dict,
    model: str = OLLAMA_MODEL_NAME,
) -> dict | None:
    """
    Call Ollama using a JSON schema and parse the returned structured output.
    """
    try:
        from ollama import chat

        response = chat(
            model=model,
            messages=messages,
            format=schema,
            options={"temperature": 0},
        )

        return json.loads(response.message.content)

    except (Exception, json.JSONDecodeError):
        return None


def generate_grounded_answer(
    question: str,
    context: str,
    model: str = OLLAMA_MODEL_NAME,
) -> str | None:
    system = f"""
You are a grounded question-answering component inside a prototype trading knowledge system.

STRICT RULES:

1. Use only facts explicitly supported by the retrieved context.

2. Do not use your own background knowledge.

3. Do not guess the meaning of an acronym, term, or concept
   if it is not defined in the retrieved context.

4. Do not introduce new causal relationships.
   If the context says that several factors are relevant,
   do not claim that one factor causes or determines the others
   unless the context explicitly states that relationship.

5. Preserve the strength of the evidence.
   If the context says "can", "may", or "can influence",
   do not strengthen it to "always", "directly causes",
   or "determines".

6. Do not add examples, formulas, or conclusions
   that are not supported by the retrieved context.

7. If the retrieved context is insufficient,
   reply exactly and only:

{REFUSAL_TEXT}

8. Otherwise:
   - answer the question directly;
   - keep the answer concise;
   - prefer paraphrasing the retrieved evidence;
   - do not add unsupported interpretation.
""".strip()

    user = (
        f"Question:\n{question}\n\n"
        f"Retrieved context:\n{context}"
    )

    return _chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        model=model,
    )


def explain_tool_result(
    question: str,
    evidence: str,
    model: str = OLLAMA_MODEL_NAME,
) -> str | None:
    system = """
You are explaining the output of a deterministic trading-data analysis tool.

Use only the supplied tool output.

Do not invent market explanations, causes, or missing numbers.

State what the data shows and distinguish observation from interpretation.

Keep the answer concise.
""".strip()

    user = (
        f"Question:\n{question}\n\n"
        f"Tool output:\n{evidence}"
    )

    return _chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        model=model,
    )

GOVERNANCE_DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "business_context": {
            "type": "string",
        },
        "evidence_used": {
            "type": "array",
            "uniqueItems": True,
            "items": {
                "type": "string",
                "enum": [
                    "field",
                    "business_definition",
                    "business_process",
                    "downstream_use",
                ],
            },
        },
    },
    "required": [
        "business_context",
        "evidence_used",
    ],
    "additionalProperties": False,
}


def generate_governance_issue_draft(
    evidence: dict,
    model: str = OLLAMA_MODEL_NAME,
) -> dict | None:
    """
    Generate only the language component of a
    governance issue draft.

    Deterministic governance facts are generated
    outside the LLM.
    """
    system = """
You are a bounded drafting component inside a controlled
data-governance workflow.

Your only task is to produce:
1. business_context;
2. evidence_used.

The supplied evidence is authoritative.

BUSINESS CONTEXT RULES:

1. Use only the supplied evidence.

2. The business_context must only restate or closely
   paraphrase:
   - what the field means;
   - which business process it belongs to;
   - its documented downstream use.

3. Do not explain why those downstream uses are important.

4. Do not infer consequences of a data-quality failure.

5. Do not introduce new systems, processes, outcomes,
   risks, reporting uses, liquidity effects, regulatory
   consequences, client impacts, financial impacts,
   operational impacts, or causal mechanisms unless
   explicitly stated in the supplied evidence.

6. Do not state or imply that the field ensures, enables,
   guarantees, protects, improves, maintains, supports
   accuracy, or is essential for an outcome unless that
   relationship is explicitly stated in the evidence.

7. Do not discuss:
   - control failure;
   - pass rate;
   - thresholds;
   - severity;
   - root cause;
   - remediation;
   - escalation;
   - issue status.

EVIDENCE ATTRIBUTION:

8. evidence_used must contain every supplied field that
   materially supports the business_context.

9. Each evidence field may appear at most once.

10. Do not list evidence that is not materially used.

Return only the structured output required by the schema.
""".strip()

    user = (
        "Authoritative business-context evidence:\n\n"
        + json.dumps(
            evidence,
            indent=2,
            ensure_ascii=False,
        )
    )

    return _chat_structured(
        [
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": user,
            },
        ],
        schema=GOVERNANCE_DRAFT_SCHEMA,
        model=model,
    )

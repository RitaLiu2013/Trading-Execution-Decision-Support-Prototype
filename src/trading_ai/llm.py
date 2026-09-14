from __future__ import annotations

from .config import OLLAMA_MODEL_NAME, REFUSAL_TEXT


def _chat(messages: list[dict], model: str = OLLAMA_MODEL_NAME) -> str | None:
    try:
        from ollama import chat
        response = chat(model=model, messages=messages, options={"temperature": 0})
        return response.message.content.strip()
    except Exception:
        return None


def generate_grounded_answer(question: str, context: str, model: str = OLLAMA_MODEL_NAME) -> str | None:
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
    user = f"Question:\n{question}\n\nRetrieved context:\n{context}"
    return _chat([{"role": "system", "content": system}, {"role": "user", "content": user}], model=model)


def explain_tool_result(question: str, evidence: str, model: str = OLLAMA_MODEL_NAME) -> str | None:
    system = """
You are explaining the output of a deterministic trading-data analysis tool.
Use only the supplied tool output. Do not invent market explanations, causes, or missing numbers.
State what the data shows, and distinguish observation from interpretation.
Keep the answer concise.
""".strip()
    user = f"Question:\n{question}\n\nTool output:\n{evidence}"
    return _chat([{"role": "system", "content": system}, {"role": "user", "content": user}], model=model)

# Trading Execution AI Prototype

A small, auditable decision-support prototype exploring how deterministic analytics and generative AI can work together in a trading-execution workflow.

The project uses a deliberately imperfect synthetic dataset of **240 trade-execution records** across equity, fixed-income and FX-style instruments. It validates data quality, calculates execution metrics, analyses venue and asset-class performance, and routes different questions either to deterministic Python analytics, grounded retrieval-augmented generation (RAG), or an unsupported-question path.

The central design principle is:

> **The LLM should not be the source of truth for calculations or record-level data.**

Numerical calculations, validation, filtering and ranking are handled deterministically in Python. The LLM is used only where natural-language explanation adds value.

The project therefore focuses as much on **data quality, system logic, controls, testing and failure handling** as on the AI component itself.

---

## Why I Built This

Trading and market-data workflows combine several different types of problems:

- exact numerical calculations;
- imperfect or inconsistent data;
- questions that require aggregation over structured records;
- domain-knowledge questions;
- ambiguous or unsupported requests.

Treating all of these as an LLM problem makes a system harder to test, explain and audit.

This prototype explores a different approach:

```text
Use deterministic code where exactness matters.
Use retrieval where domain knowledge is needed.
Use an LLM where natural-language explanation adds value.
Keep the boundaries between those components explicit.
```

The objective is not to build a production trading system.

Instead, the project demonstrates how analytical, data-quality and AI components can be combined in a transparent and testable decision-support workflow.

---

## What the Project Demonstrates

### Trading and Execution Analytics

- Synthetic trading-data modelling with deterministic reproducibility.
- Side-adjusted execution metrics so adverse BUY and SELL executions have a consistent interpretation.
- Venue-level and asset-class execution analysis.
- Identification of worst executions and partial fills.
- Comparison of mean, median and 90th-percentile slippage rather than relying on averages alone.

### Data-Quality Controls

- Duplicate trade-ID detection.
- Missing benchmark detection.
- Invalid execution quantities.
- Dirty categorical values.
- Separation of hard data errors from unusual but structurally valid observations.
- Explicit construction of analysis-ready populations.

### Applied AI

- Grounded RAG over a small trading-execution knowledge base.
- Semantic retrieval using embeddings.
- Routing between structured analytics, knowledge retrieval and unsupported questions.
- Local LLM integration using Ollama.
- Clear separation between deterministic calculations and generative explanation.

### Testing and Auditability

- Unit and deterministic tests for numerical logic.
- Known injected data-quality failures.
- Retrieval evaluation.
- Routing evaluation.
- Unsupported-question handling.
- Explicit assumptions and limitations.

---

## Architecture

```text
                         User Question
                               |
                               v
                         Question Router
                               |
             +-----------------+-----------------+
             |                                   |
             v                                   v
      Structured Data                      Knowledge Question
          Question                                |
             |                                    v
             v                            Semantic Retrieval
      Python Data Tools                            |
             |                                    v
     Validation / Metrics                    Top-k Context
             |                                    |
             v                                    v
     Deterministic Result                     Local LLM
             |                                    |
             +-----------------+------------------+
                               |
                               v
                       Grounded Response


Unsupported / out-of-domain question
                |
                v
        Unsupported Route
```

The numerical layer remains deterministic.

The LLM does not calculate execution metrics, count records, detect duplicates or determine which observations belong in an analytical population.

---

## Synthetic Dataset

The repository contains **240 synthetic trade-execution records** across:

- Equity;
- Fixed Income;
- FX-style instruments.

The dataset is intentionally imperfect.

Several cases are deliberately injected so that the analytical workflow has to distinguish between data-quality failures and legitimate but unusual observations.

Examples include:

- a **35% partial fill** that is unusual but not automatically a data error;
- a missing arrival-price benchmark;
- an executed quantity greater than order quantity;
- a duplicate trade ID;
- an approximately **900 bps adverse execution outlier**;
- a dirty categorical value such as `" buy "`;
- a missing VWAP benchmark.

A key principle of the project is:

> **Unusual outcome ≠ bad data.**

Hard validation failures are excluded from the relevant analytical universe.

Extreme but structurally valid observations are retained and flagged for investigation rather than automatically removed.

---

## Data-Quality Workflow

The control workflow follows a simple sequence:

```text
Raw synthetic trades
        |
        v
Schema and required-field checks
        |
        v
Business-rule validation
        |
        v
Data-quality classification
        |
        +------------------------+
        |                        |
        v                        v
Hard validation failure     Valid / unusual record
        |                        |
        v                        v
Exclude where required      Retain for analysis
                                 |
                                 v
                         Flag where appropriate
```

The objective is not simply to produce a "clean" dataset.

It is to make the reason for including, excluding or flagging an observation explicit.

---

## Core Execution Metric

The prototype uses a simplified side-adjusted arrival-price deviation.

```text
side_sign = +1 for BUY
side_sign = -1 for SELL

signed_arrival_slippage_bps =
    side_sign
    * (avg_execution_price - arrival_price)
    / arrival_price
    * 10,000
```

Positive values therefore consistently indicate execution worse than the arrival benchmark for both BUY and SELL records.

For example:

- BUY above arrival price → adverse → positive slippage;
- SELL below arrival price → adverse → positive slippage.

This is an illustrative execution metric and **not a complete implementation-shortfall model**.

---

## Structured Execution Analytics

The deterministic analytical layer can answer questions such as:

```text
Which venue has the worst average execution slippage?

Which asset class has the highest 90th-percentile slippage?

Show the five worst executions.

Which trades are partial fills?

What data-quality issues are present?
```

The calculations are performed in Python before any natural-language explanation is generated.

The analytical workflow includes:

- venue-level summaries;
- asset-class summaries;
- worst-execution analysis;
- partial-fill analysis;
- data-quality reporting;
- analysis-ready populations.

Generated outputs include:

```text
outputs/
├── asset_class_summary.csv
├── data_quality_summary.csv
├── evaluation_report.md
└── venue_summary.csv
```

---

## Why Mean Slippage Is Not Enough

Execution data can contain large but legitimate outliers.

For this reason, venue and asset-class summaries include:

- mean slippage;
- median slippage;
- 90th-percentile slippage.

An extreme observation may materially affect the mean while leaving the median relatively stable.

Instead of deleting such an observation automatically, the system keeps it visible so that an analyst can determine whether it represents:

- bad data;
- a genuine execution event;
- or a case requiring further investigation.

This reflects a broader design principle of the project:

> **An anomaly should first be understood before it is removed.**

---

## Knowledge Retrieval and RAG

Some questions cannot be answered from the structured trade dataset.

Examples include:

```text
What is implementation shortfall?

Why can liquidity affect execution quality?

What are common components of execution cost?
```

These questions are routed to a small trading-execution knowledge base.

The RAG pipeline follows:

```text
Knowledge documents
        |
        v
Chunking
        |
        v
Embeddings
        |
        v
Semantic retrieval
        |
        v
Top-k context
        |
        v
Local LLM
        |
        v
Grounded explanation
```

The LLM is instructed to answer from retrieved evidence rather than invent unsupported information.

---

## Routing Logic

Different questions require different system components.

| Question | Route | Reason |
|---|---|---|
| What is implementation shortfall? | Knowledge / RAG | Requires domain knowledge |
| Why can liquidity affect execution quality? | Knowledge / RAG | Requires explanatory knowledge |
| Which venue has the worst average slippage? | Data tool | Requires deterministic aggregation |
| Show the top 5 worst executions | Data tool | Requires exact filtering and sorting |
| What data-quality issues are present? | Data tool | Requires record-level validation |
| What problem does MCP solve? | Unsupported | Outside the trading-execution domain |
| How do I make pizza? | Unsupported | Outside project scope |

The routing logic is deterministic rather than agentic.

For a small and bounded system, predictable routing makes behaviour easier to inspect, test and debug.

---

## Why the LLM Does Not Perform the Calculations

A language model should not be the system of record for:

- exact row counts;
- arithmetic;
- duplicate detection;
- benchmark calculations;
- filtering;
- sorting;
- record-level truth.

Python produces the analytical evidence first.

The LLM may then explain already-computed results where natural-language interpretation is useful.

This produces a clearer audit trail and makes it easier to determine whether a problem occurred in:

```text
data
  ↓
validation
  ↓
calculation
  ↓
routing
  ↓
retrieval
  ↓
generation
```

rather than treating every incorrect output as a generic "AI failure."

---

## Evaluation Strategy

The project evaluates different system components separately rather than relying on one broad answer-quality score.

### 1. Data Quality

Known injected failures should be detected correctly.

Examples include:

- duplicate IDs;
- missing required benchmarks;
- invalid quantities;
- malformed categories.

### 2. Metric Correctness

Constructed BUY and SELL examples test whether adverse executions consistently produce positive sign-adjusted slippage.

### 3. Routing

Representative questions are checked against their expected route:

```text
structured data
knowledge retrieval
unsupported
```

### 4. Retrieval

Knowledge questions are evaluated to determine whether relevant source material appears within the Top-k retrieved chunks.

### 5. Scope and Refusal

Out-of-domain questions should not be treated as valid trading-knowledge requests.

Evaluation logic is implemented in:

```text
src/trading_ai/evaluation.py
```

and summarised in:

```text
outputs/evaluation_report.md
```

---

## Design Decisions and Trade-offs

### 1. Workflow Before Agent

The current router is deterministic by design.

An autonomous agent would add flexibility, but it would also make control flow and failure attribution harder to inspect.

For a small and bounded prototype, deterministic routing provides a useful baseline.

Tool-calling or more agentic routing would make sense only after the underlying data tools and evaluation framework are stable.

### 2. Deterministic Analytics Before Generative Explanation

Structured-data questions are answered using Python tools rather than asking the LLM to reason over raw rows.

This creates a clear separation between:

```text
calculation
```

and:

```text
explanation
```

The approach improves transparency and makes numerical errors easier to identify.

### 3. No Arbitrary Cosine-Similarity Threshold

Cosine similarity is a ranking signal, not a calibrated probability.

The prototype therefore does not assume that a universal threshold such as:

```text
similarity > 0.5
```

automatically means that a retrieved chunk is sufficiently relevant.

A production implementation would require a larger labelled evaluation set to calibrate relevance gating properly.

### 4. Hard Errors and Unusual Outcomes Are Different

A missing benchmark or impossible execution quantity can invalidate a calculation.

A 35% partial fill or very poor execution result may instead represent a genuine business event.

The prototype therefore distinguishes:

```text
data-quality failure
!=
unusual business outcome
```

This distinction determines whether an observation is:

- excluded;
- retained;
- or flagged for investigation.

### 5. Synthetic Relationships Are Known by Construction

The synthetic-data generator deliberately includes relationships involving variables such as:

- spread;
- volatility;
- participation rate;
- venue;
- asset class.

Any relationship observed in the generated dataset is therefore a **pipeline-validation feature**, not an empirical market finding and not evidence of causality.

---

## Repository Structure

```text
.
├── data/
│   └── synthetic_trades.csv
│
├── knowledge/
│   ├── execution_cost_notes.txt
│   ├── execution_risk_notes.txt
│   ├── liquidity_notes.txt
│   └── SOURCES.md
│
├── notebooks/
│   └── trading_execution_ai_demo.ipynb
│
├── outputs/
│   ├── asset_class_summary.csv
│   ├── data_quality_summary.csv
│   ├── evaluation_report.md
│   └── venue_summary.csv
│
├── src/
│   └── trading_ai/
│       ├── analytics.py
│       ├── cli.py
│       ├── config.py
│       ├── evaluation.py
│       ├── llm.py
│       ├── metrics.py
│       ├── rag.py
│       ├── router.py
│       ├── synthetic_data.py
│       ├── validation.py
│       └── workflow.py
│
└── tests/
```

---

## Quick Start

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on macOS / Linux:

```bash
source .venv/bin/activate
```

### 2. Install the project

```bash
pip install -e ".[dev]"
```

### 3. Regenerate the deterministic synthetic dataset

This step is optional if the generated dataset is already present.

```bash
python -m trading_ai.synthetic_data
```

### 4. Run the tests

```bash
pytest
```

### 5. Run deterministic evaluation

```bash
trading-ai --evaluate
```

### 6. Ask structured-data questions without an LLM

```bash
trading-ai --no-llm -q "Which venue has the worst average execution slippage?"
trading-ai --no-llm -q "Show the top 5 worst executions"
trading-ai --no-llm -q "What data quality issues are present?"
```

### 7. Enable the local LLM / RAG path

The repository is configured for a local Ollama model:

```text
qwen3:4b-instruct
```

Pull and run the model:

```bash
ollama pull qwen3:4b-instruct
ollama run qwen3:4b-instruct
```

Then, in another terminal:

```bash
trading-ai -q "What is implementation shortfall?"
trading-ai -q "Why can liquidity affect execution quality?"
```

The first SentenceTransformer run may download the configured embedding model.

---

## Example Workflow Behaviour

| Question | Expected System Behaviour |
|---|---|
| What is implementation shortfall? | Retrieve relevant knowledge and generate a grounded explanation |
| Why can liquidity affect execution quality? | Use RAG over the trading knowledge base |
| Which venue has the worst average execution slippage? | Calculate the answer deterministically from structured data |
| Show the top five worst executions | Filter and rank records using Python |
| What data-quality issues are present? | Return validation results |
| What problem does MCP solve? | Route as unsupported |
| How do I make Italian pizza? | Route as unsupported |

The objective is not for one model to answer every possible question.

The objective is for each type of question to be handled by the most appropriate system component.

---

## Limitations

This is an educational and portfolio prototype.

It is **not**:

- a production transaction-cost-analysis system;
- an execution algorithm;
- an investment recommendation;
- a representation of any employer's methodology;
- a model trained on confidential trading data.

Additional limitations include:

- all trade data are synthetic;
- synthetic market relationships are known by construction;
- cross-asset quantities and notionals are simplified;
- execution metrics are intentionally limited and do not reproduce a full implementation-shortfall or TCA framework;
- the router supports a bounded set of question types rather than open-ended planning;
- the RAG knowledge base and evaluation set are intentionally small;
- the local LLM can still violate grounding instructions.

Deterministic evidence therefore remains visible and inspectable throughout the workflow.

---

## Possible Extensions

Potential next steps include:

- SQL-backed analytical tools instead of in-memory pandas;
- dbt-style transformations and data-quality tests;
- calibrated relevance gating using a larger labelled evaluation set;
- reranking for semantically similar but answer-irrelevant chunks;
- optional tool-calling after deterministic routing baselines are stable;
- more realistic order-life-cycle and benchmark data;
- richer transaction-cost and implementation-shortfall metrics;
- formal functional requirements and acceptance-test cases;
- a larger evaluation suite for retrieval and grounded generation.

These extensions are deliberately separated from the current implementation so that the repository remains clear about what has already been built and what is planned.

---

## Public References

The knowledge notes use public educational material, including:

- CFA Institute — *Trading Costs and Electronic Markets*
- Investor.gov — *Understanding Order Types – Investor Bulletin*
- Investor.gov — *Executing an Order*

The source list used by the project is documented in:

```text
knowledge/SOURCES.md
```

---

## Short Project Summary

I built a small trading-execution decision-support prototype that separates deterministic quantitative analysis from generative AI.

The system validates deliberately imperfect synthetic trade data, calculates sign-adjusted execution metrics, routes structured questions to Python tools, uses grounded RAG for domain-knowledge questions, and evaluates failures separately across data quality, numerical logic, routing and retrieval.

A central design choice was to keep calculations and record-level truth outside the LLM, using generative AI only where natural-language explanation adds value.

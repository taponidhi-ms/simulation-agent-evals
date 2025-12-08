# Copilot Instructions

This document provides guidance for GitHub Copilot when working with this repository.

## Project Overview

This is a Python-based simulation agent evaluation project.

## Coding Standards

- Follow PEP 8 style guidelines for Python code
- Use meaningful variable and function names
- Include docstrings for functions and classes
- Add type hints where appropriate

## Testing

- Write unit tests for new functionality
- Ensure existing tests pass before submitting changes

## Development Workflow

- Make small, focused commits
- Write clear commit messages
- Update documentation when making changes to public APIs

## CXA Evals Framework - Metrics Overview

This section provides detailed information about the evaluator types and metrics used in the CXA Evals framework for evaluating agent performance.

### 1. OOB / Default Evaluator Metrics

The **DefaultEvaluator** (Out‑of‑Box / OOB) applies a standard set of **domain‑agnostic** quality metrics.  
Any partner team can use these to evaluate the quality of their outputs.  
Each metric is scored independently on a **0–10 scale**, where higher scores indicate stronger performance. _[there is ongoing research by the team on the scale ranges]_

| **Metric**           | **Definition** |
|----------------------|----------------|
| **Accuracy**         | Measures how well the response matches the ground truth in correctness and coverage; penalizes contradictions and major omissions. |
| **Groundedness**     | Ensures the response is strictly supported by the provided ground truth/reference, avoiding unsupported or hallucinated details. |
| **Completeness**     | Assesses whether the response fully covers all essential aspects of the query/task without missing key details. |
| **Relevance**        | Checks that the response stays on-topic and aligned with the user's intent and context, avoiding unrelated content. |
| **Noise Sensitivity**| Evaluates robustness to minor, irrelevant variations in the input; a robust system gives consistent answers despite small "noise." |
| **Conversationality**| Rates clarity, readability, natural flow, and tone; ensures structure and wording are appropriate for the intended audience. |

---

### 2. CustomEvaluator

The **CustomEvaluator** enables teams to define **their own metric set** or adjust metric weighting to fit domain‑specific needs.

**Definition:**  
Designed for scenarios where the default metrics are not sufficient or need to be adapted. Partner teams can:
- Add new metrics relevant to their domain (e.g., Legal Compliance, Brand Voice).
- Adjust scoring weights to emphasize certain quality dimensions over others.
- Incorporate domain‑specific definitions for existing metrics.

#### Example: *Product FAQ Response* Use Case

This example shows how a partner team could use **DefaultEvaluator** and **CustomEvaluator** to setup OOB and custom metrics to evaluate responses for customer questions about a product FAQ.  
The rules adapt the default metrics to emphasize **brand tone**, **policy compliance**, and **source alignment**.

| **Metric** | **Custom Definition** |
|------------|------------------------|
| **Accuracy** | All product details (e.g., specifications, pricing, warranty terms) must exactly match the official product documentation or approved FAQ content. No fabricated or outdated information is allowed. Uses `{groundness_fact}` from input data. |
| **Groundedness** | Every fact must be directly traceable to the approved FAQ or product documentation. Additional context must be clearly marked as "additional guidance" and must not contradict the source. |
| **Completeness** | The response must address all parts of the customer's question, including sub‑questions, and provide all relevant details from the FAQ. |
| **Relevance** | The content must focus only on the product(s) and topics mentioned in the customer's question. Avoid unrelated product information or marketing filler. |
| **Usefulness** | The answer must provide clear, actionable information that helps the customer make a decision or take the next step (e.g., how to order, how to claim warranty). |
| **Conversationality** | The tone should reflect the brand's voice: friendly, professional, and easy to understand. Avoid overly technical jargon unless the audience expects it. |
| **Policy Compliance** *(Custom)* | The response must follow brand communication guidelines, avoid prohibited claims, and comply with all legal and regulatory requirements for the product category. |

**When to Use:**
- If **OOB Evals** do not fully capture your quality requirements.  
- When aligning evaluation with **custom rules** such as brand tone, legal compliance, or industry‑specific standards.  
- For scenarios where **policy adherence** is as important as factual correctness.

---

### 3. GroundnessEvaluator

 
**Purpose:**  
A specialized evaluator that measures how well an output is **anchored to authoritative source material**.  
Ideal for scenarios where **source fidelity** is the primary quality requirement — ensuring every fact, figure, or statement can be traced back to a trusted reference.

**Definition:**  
Groundedness is the degree to which an output:
- **Directly reflects** the provided source data, documents, or knowledge base.
- **Avoids fabrication** — no invented facts, examples, or details outside the source.
- **Clearly marks** any additional context or interpretation as such, without presenting it as sourced fact.

**Evaluation Criteria:**
- **Source Alignment:** All factual statements match the authoritative source exactly in meaning.
- **Traceability:** Each fact or metric can be linked to a specific location in the source material.
- **No Unsupported Claims:** No speculative or inferred content unless explicitly labeled as such.

**When to Use:**
- When validating that generated content **strictly adheres** to provided source material.
- In compliance‑sensitive workflows where **traceability** is mandatory (e.g., legal, medical, financial).
- For partner teams that need to **audit outputs** against a fixed dataset or document set.
- When **OOB Evals** are too broad and you need a **single‑focus check** on source fidelity.


**Tip:**  
If you only care about **whether the output is faithful to the source**, and not about tone, completeness, or actionability, run the **GroundnessEvaluator** on its own for a fast, focused check.

---

### 4. Scoring Scale Tokens

| **Token** | **Value** | **Meaning** |
|-----------|-----------|-------------|
| **LowScore** | `"0"` | Does not meet the metric's basic requirements. |
| **HighScore** | `"10"` | Fully meets or exceeds the metric's requirements. |

> Scores between **1–9** reflect partial fulfillment of the metric. This is fully customizable through configuration.

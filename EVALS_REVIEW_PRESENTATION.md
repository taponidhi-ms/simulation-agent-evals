# SimulationAgent Evals Process - Product Presentation

## Executive Summary

This document presents the complete evaluation (evals) process for the SimulationAgent feature in Dynamics 365 Customer Service. The process consists of five main stages:

1. **User Input**: Providing natural language prompts describing simulation scenarios
2. **Persona Generation**: Creating diverse customer personas from natural language prompts
3. **Conversation Generation**: Generating realistic conversations between customers and CSR agents
4. **Evaluation**: Assessing the quality of both personas and conversations using custom evaluation rules
5. **Analysis & Improvement**: Reviewing results and iterating to enhance quality

---

## Table of Contents

- [1. Overall Evals Process Flow](#1-overall-evals-process-flow)
  - [Key Components Explanation](#key-components-explanation)
- [2. Persona Generation Process](#2-persona-generation-process)
  - [2.1 Flow Diagram](#21-flow-diagram)
  - [2.2 System Prompt for Persona Generation](#22-system-prompt-for-persona-generation)
  - [2.3 Example Input and Output](#23-example-input-and-output)
  - [2.4 Persona Generation Evaluation Rules](#24-persona-generation-evaluation-rules)
  - [2.5 Output Files for Persona Evaluation](#25-output-files-for-persona-evaluation)
- [3. Conversation Generation Process](#3-conversation-generation-process)
  - [3.1 Flow Diagram](#31-flow-diagram)
  - [3.2 Customer Agent Prompt Template](#32-customer-agent-prompt-template)
  - [3.3 CSR Agent Prompt Template](#33-csr-agent-prompt-template)
  - [3.4 Sample Conversation Flow](#34-sample-conversation-flow)
  - [3.5 Orchestrator Logic](#35-orchestrator-logic)
  - [3.6 Conversation Evaluation Rules](#36-conversation-evaluation-rules)
  - [3.7 Output Files for Conversation Evaluation](#37-output-files-for-conversation-evaluation)
- [4. CXA Evals Framework Integration](#4-cxa-evals-framework-integration)
  - [4.1 Evaluator Types Used](#41-evaluator-types-used)
  - [4.2 How CXA Evals Works](#42-how-cxa-evals-works)
  - [4.3 Variable Substitution](#43-variable-substitution)
- [5. Improvement Recommendations Based on Eval Results](#5-improvement-recommendations-based-on-eval-results)
  - [5.1 Interpreting Evaluation Results](#51-interpreting-evaluation-results)
  - [5.2 Persona Generation Improvements](#52-persona-generation-improvements)
  - [5.3 Conversation Generation Improvements](#53-conversation-generation-improvements)
  - [5.4 Knowledge Base Improvements](#54-knowledge-base-improvements)
  - [5.5 Model Configuration Tuning](#55-model-configuration-tuning)
  - [5.6 Iterative Improvement Process](#56-iterative-improvement-process)
- [6. Output Structure and File Organization](#6-output-structure-and-file-organization)
  - [6.1 Complete Directory Structure](#61-complete-directory-structure)
  - [6.2 Traceability](#62-traceability)
- [7. Key Metrics and Success Criteria](#7-key-metrics-and-success-criteria)
  - [7.1 Quality Metrics](#71-quality-metrics)
  - [7.2 Operational Metrics](#72-operational-metrics)
- [8. Frequently Asked Questions](#8-frequently-asked-questions)
- [9. Next Steps](#9-next-steps)
  - [For Product Teams](#for-product-teams)
  - [For Implementation](#for-implementation)
  - [For Continuous Improvement](#for-continuous-improvement)
- [Appendix A: Configuration Reference](#appendix-a-configuration-reference)
  - [Persona Generator Configuration](#persona-generator-configuration)
  - [Conversation Generator Configuration](#conversation-generator-configuration)
  - [CXA Evals Configuration](#cxa-evals-configuration)
- [Appendix B: Example Commands](#appendix-b-example-commands)
  - [Generate Personas](#generate-personas)
  - [Generate Conversations](#generate-conversations)
  - [Run CXA Evals](#run-cxa-evals)

---

## 1. Overall Evals Process Flow

```mermaid
flowchart TB
    subgraph Input["1. User Input"]
        A[Natural Language Prompt<br/>Describing Scenario]
    end
    
    subgraph PersonaGen["2. Persona Generation"]
        B[LLM with System Prompt] --> C[Generate Personas JSON]
        C --> D[Validate Structure]
        D --> E[Save to personas_YYYYMMDD_HHMMSS/]
        E --> F[Transform to CXA Evals Format]
        F --> G[Create Persona Eval Config]
    end
    
    subgraph ConvGen["3. Conversation Generation"]
        H[Load Personas] --> I[Initialize Customer & CSR Agents]
        I --> J[For Each Persona:<br/>Generate 1 Conversation]
        J --> K[Orchestrator Manages Turn-Taking]
        K --> L[Save Conversations to JSON]
        L --> M[Transform to CXA Evals Format]
        M --> N[Create Conversation Eval Config]
    end
    
    subgraph Evaluation["4. CXA Evals Evaluation"]
        O[CXA Evals Framework] --> P[Evaluate Persona Generation]
        O --> Q[Evaluate Conversation Quality]
        P --> R[Persona Eval Results]
        Q --> S[Conversation Eval Results]
    end
    
    subgraph Analysis["5. Analysis & Improvement"]
        T[Review Eval Results] --> U[Identify Issues]
        U --> V[Implement Improvements]
        V --> W[Re-run & Validate]
    end
    
    A --> B
    E --> H
    G --> P
    N --> Q
    R --> T
    S --> T
    
    style A fill:#e1f5e1
    style C fill:#fff4e1
    style J fill:#fff4e1
    style F fill:#d4f4ff
    style M fill:#d4f4ff
    style O fill:#e1e5ff
    style T fill:#ffe1e1
```

### Key Components Explanation

1. **User Input**: A natural language prompt describing the simulation scenario (e.g., "Create 10 customer personas for a flower delivery company with 50% calm and 50% frustrated customers")

2. **Persona Generation**: An LLM extracts structured persona data from the prompt, including name, description, goal, tone, and complexity level

3. **Conversation Generation**: For each persona, a two-agent system (Customer + CSR) generates a realistic conversation with turn-taking managed by an orchestrator

4. **CXA Evals Evaluation**: Both persona generation and conversation quality are evaluated against custom rules using the CXA Evals framework

5. **Analysis & Improvement**: Results are analyzed to identify areas for improvement in prompt engineering, persona diversity, or conversation quality

---

## 2. Persona Generation Process

### 2.1 Flow Diagram

```mermaid
flowchart LR
    A[User Prompt] --> B[System Prompt<br/>+ User Prompt]
    B --> C[Azure OpenAI LLM<br/>gpt-4o-mini]
    C --> D{Valid JSON?}
    D -->|No| E[Extract from<br/>Markdown Block]
    D -->|Yes| F[Validate Structure]
    E --> F
    F --> G{Has Required<br/>Fields?}
    G -->|No| H[Error: Missing Fields]
    G -->|Yes| I[Save personas.json]
    I --> J[Save Metadata]
    J --> K[Transform to<br/>CXA Evals Format]
    K --> L[Create Eval Config]
    L --> M[Output Directory:<br/>personas_YYYYMMDD_HHMMSS/]
    
    style A fill:#e1f5e1
    style C fill:#fff4e1
    style I fill:#d4f4ff
    style K fill:#d4f4ff
    style M fill:#ffe1e1
```

### 2.2 System Prompt for Persona Generation

The following is the **exact system prompt** given to the LLM for persona generation:

```
You are an expert at creating customer personas for customer service simulation scenarios.

Given a natural language description of a simulation scenario, extract and generate a structured list of customer personas.

Each persona should include:
- name: A descriptive name for the persona (e.g., "Frustrated Refund Seeker")
- description: A detailed description of the customer's situation and behavior
- goal: What the customer wants to achieve
- tone: The expected tone/emotion of the customer (e.g., "frustrated but trying to remain civil")
- complexity: The complexity level of the interaction (simple, medium, or complex)

IMPORTANT: You must respond ONLY with valid JSON in exactly this format:
{
  "personas": [
    {
      "name": "Persona Name",
      "description": "Detailed description",
      "goal": "What they want to achieve",
      "tone": "Their emotional tone",
      "complexity": "simple|medium|complex"
    }
  ]
}

LIMIT: If the user's prompt requests more than 50 personas, return an empty list: {"personas": []}

Do NOT include any other text, explanations, or markdown formatting. Only output the JSON object.
```

### 2.3 Example Input and Output

**Input Prompt:**
```
Simulate 10 conversations between customers and agent. Agents belong to a company 
like https://www.1800flowers.com/ which sells flowers to customers. 50% customers 
should behave as either calm and composed and other 50% should behave as angry or 
disappointed. They have varying kinds of issues normally faced by customers of 
1800flowers type company.
```

**Output (personas.json):**
```json
{
  "personas": [
    {
      "name": "Calm Order Inquiry",
      "description": "Customer wants to check the status of their flower delivery order",
      "goal": "Get an update on when flowers will arrive",
      "tone": "polite and patient",
      "complexity": "simple"
    },
    {
      "name": "Disappointed Wedding Flowers",
      "description": "Customer's wedding flowers arrived wilted and damaged",
      "goal": "Get a refund and express disappointment",
      "tone": "disappointed and upset",
      "complexity": "complex"
    }
  ],
  "_note": "... 8 more personas would be included here in actual output",
  "_metadata": {
    "generated_at": "2025-12-09T14:06:11.123456",
    "timestamp": "20251209_140611",
    "prompt": "Simulate 10 conversations...",
    "num_personas": 10
  }
}
```

### 2.4 Persona Generation Evaluation Rules

The quality of persona generation is evaluated using **5 custom rules**:

| Rule Name | Category | Description |
|-----------|----------|-------------|
| **persona_diversity** | Content | Generated personas must have diverse tones, goals, and complexity levels based on the prompt requirements |
| **persona_completeness** | Completeness | Each persona must include all required fields: name, description, goal, tone, and complexity |
| **persona_relevance** | Relevance | Personas must be relevant to the scenario described in the user's prompt |
| **persona_distribution** | Accuracy | Personas must match the requested distribution (e.g., if prompt requests 50% calm and 50% angry, the generated personas should reflect this) |
| **persona_count_accuracy** | Accuracy | The number of personas generated must match the number requested in the prompt. If > 50 requested, should return empty list |

**Scoring:**
- Scale: 1 (Low) to 10 (High)
- Threshold: 7 (scores below 7 indicate issues)
- Format: Single-turn evaluation (one prompt → one response)

### 2.5 Output Files for Persona Evaluation

```
conversation_generator/personas/personas_20251209_140611/
├── personas.json                                    # Generated personas with metadata
├── _metadata.json                                   # Metadata (backward compatibility)
├── cxa_evals_personas.json                          # CXA Evals format
├── cxa_evals_persona_generator_custom_config.json   # Evaluation configuration
└── cxa-evals-output/                                # Evaluation results (after running CXA Evals)
```

---

## 3. Conversation Generation Process

### 3.1 Flow Diagram

```mermaid
flowchart TD
    A[Load Personas JSON] --> B[Initialize Azure OpenAI Client]
    B --> C[Load Knowledge Base<br/>FAQs & Policies]
    C --> D{For Each Persona}
    
    D --> E[Create Customer Agent<br/>with Persona Context]
    E --> F[Create CSR Agent<br/>with Knowledge Base]
    
    F --> G[Initialize Orchestrator]
    G --> H[Customer: Initial Message]
    
    H --> I{Conversation Loop}
    I --> J[CSR: Generate Response<br/>using Knowledge Base]
    J --> K{CSR Escalated?}
    
    K -->|Yes| L[Status: ESCALATED<br/>End Conversation]
    K -->|No| M[Customer: Generate Response<br/>based on Persona]
    
    M --> N{Customer Satisfied?}
    N -->|Yes| O[Status: RESOLVED<br/>End Conversation]
    N -->|No| P{Max Turns<br/>Reached?}
    
    P -->|Yes| Q[Status: RESOLVED<br/>Max Turns]
    P -->|No| I
    
    L --> R[Save Conversation JSON]
    O --> R
    Q --> R
    
    R --> S{More Personas?}
    S -->|Yes| D
    S -->|No| T[Save Metadata]
    
    T --> U[Transform to CXA Evals Format]
    U --> V[Create Conversation Eval Config]
    V --> W[Output: conversations_YYYYMMDD_HHMMSS/]
    
    style A fill:#e1f5e1
    style H fill:#fff4e1
    style J fill:#fff9e1
    style M fill:#fff4e1
    style U fill:#d4f4ff
    style W fill:#ffe1e1
```

### 3.2 Customer Agent Prompt Template

The Customer Agent uses a **persona-driven prompt** that is dynamically constructed for each conversation:

```
You are simulating a customer with the following characteristics:

Persona: {persona_name}
Situation: {persona_description}
Goal: {persona_goal}
Tone: {persona_tone}

You are interacting with a customer service representative. Stay in character and 
communicate naturally as this customer would. Be realistic - ask follow-up questions,
express emotions appropriately, and react to the CSR's responses.
```

**Example for "Disappointed Wedding Flowers" Persona:**
```
You are simulating a customer with the following characteristics:

Persona: Disappointed Wedding Flowers
Situation: Customer's wedding flowers arrived wilted and damaged
Goal: Get a refund and express disappointment
Tone: disappointed and upset

You are interacting with a customer service representative. Stay in character and 
communicate naturally as this customer would. Be realistic - ask follow-up questions,
express emotions appropriately, and react to the CSR's responses.
```

**Customer Agent Behavior:**
- Uses Azure OpenAI (deployment: `gpt-4o-mini`)
- Temperature: 0.7 (allows natural variation)
- Max tokens: 500 per response
- Maintains conversation history for context
- Stays in character based on persona traits

### 3.3 CSR Agent Prompt Template

The CSR Agent uses a **knowledge-based prompt** that includes the FAQ database:

```
You are a helpful and professional customer service representative.

Your role is to:
1. Assist customers with their inquiries using the knowledge base provided
2. Be polite, empathetic, and solution-oriented
3. If you cannot help with a request or it's outside your scope, politely end the 
   conversation with "I'll transfer you to a supervisor for further assistance."

KNOWLEDGE BASE:
{knowledge_base_context}

Guidelines:
- Keep responses concise and helpful
- Use information from the knowledge base when available
- Be empathetic to customer concerns
- If the customer's issue cannot be resolved with available knowledge, escalate
- Do not make up information not in the knowledge base
```

**Knowledge Base Example (Flower Delivery):**
```
KNOWLEDGE BASE:

Category: Delivery
Q: What are your delivery options?
A: We offer same-day delivery, next-day delivery, and scheduled delivery up to 
   30 days in advance. Same-day delivery is available for orders placed before 2 PM 
   in most areas.

Category: Quality Issues
Q: What if my flowers arrive damaged?
A: We guarantee freshness. If flowers arrive damaged or wilted, contact us within 
   24 hours with photos. We'll send a replacement bouquet at no charge or issue a 
   full refund.

Category: Refunds
Q: What is your refund policy?
A: Full refunds are available within 7 days of delivery for quality issues. 
   For order cancellations, refunds are issued if cancelled at least 24 hours 
   before delivery time.

[... 10-15 total FAQ items]
```

**CSR Agent Behavior:**
- Uses Azure OpenAI (deployment: `gpt-4o-mini`)
- Temperature: 0.7 (balances consistency with natural responses)
- Max tokens: 500 per response
- Accesses up to 15 knowledge base items at a time
- Detects escalation keywords to transfer to supervisor
- Provides empathetic, solution-oriented responses

### 3.4 Sample Conversation Flow

**Persona:** Disappointed Wedding Flowers  
**Complexity:** Complex

| Turn | Role | Message |
|------|------|---------|
| 1 | **Customer** | "Hi, I'm extremely disappointed. I ordered flowers for my daughter's wedding yesterday and they arrived completely wilted. This was supposed to be a special day and the flowers looked awful in all the photos. I need to speak to someone about this right away." |
| 2 | **CSR** | "I'm so sorry to hear about this experience, especially for such an important occasion as your daughter's wedding. This is absolutely not the quality we stand for. I can help you with this right now. Could you please provide your order number so I can pull up the details and arrange either a full refund or a replacement bouquet?" |
| 3 | **Customer** | "The order number is FL-2024-789012. Honestly, a replacement won't help now - the wedding is over. I just want my money back. How long will that take?" |
| 4 | **CSR** | "I completely understand, and I apologize again for ruining such a memorable moment. I'm processing a full refund for order FL-2024-789012 right now. You should see the refund in your account within 3-5 business days. Additionally, I'd like to offer you a 20% discount code for your next order as a gesture of our sincere apologies. Would you like me to email that to you?" |
| 5 | **Customer** | "That's appreciated. Yes, please send the discount code. I hope you can improve your quality control so this doesn't happen to other customers." |
| 6 | **CSR** | "Thank you for your understanding, and you're absolutely right - I'm forwarding your feedback to our quality team. I've sent the discount code to your email on file. Is there anything else I can help you with today?" |
| 7 | **Customer** | "No, that's all. Thank you for handling this quickly." |
| 8 | **CSR** | "You're very welcome, and once again, I apologize for the inconvenience. We hope to serve you better in the future. Have a great day!" |

**Status:** RESOLVED  
**Turn Count:** 8  
**Resolution Reason:** Issue resolved

### 3.5 Orchestrator Logic

The **Orchestrator** manages the conversation flow with these rules:

| Condition | Action |
|-----------|--------|
| **Start** | Customer sends initial message based on persona |
| **Turn Limit** | Max 20 turns (configurable) |
| **Customer Satisfied** | Detects keywords: "thank you", "thanks", "perfect", "great", "that works" (without questions) → Status: RESOLVED |
| **CSR Escalates** | Detects phrases: "transfer to supervisor", "escalate to", "speak with a manager" → Status: ESCALATED |
| **Max Turns Reached** | Conversation ends → Status: RESOLVED (max turns) |
| **Error** | Any generation error → Status: FAILED |

### 3.6 Conversation Evaluation Rules

The quality of generated conversations is evaluated using **3 custom rules**:

| Rule Name | Category | Description |
|-----------|----------|-------------|
| **persona_adherence** | Conversationality | The Customer should maintain consistency with their assigned persona throughout the conversation. The Customer's persona is: {{persona_name}} - {{persona_description}}. The Customer should communicate with the tone: {{persona_tone}}. |
| **goal_pursuit** | Usefulness | The Customer should actively work towards achieving their goal: {{persona_goal}}. The Customer's messages should reflect their intent to accomplish this goal. |
| **complexity_appropriate** | Conversationality | The Customer's behavior and communication should align with the expected complexity level: {{persona_complexity}}. This includes the depth of questions, technical understanding, and patience level. |

**Note:** These rules evaluate the **Customer agent's performance**, not the CSR agent. The focus is on whether the simulated customer behaves realistically according to their persona.

**Scoring:**
- Scale: 1 (Low) to 10 (High)
- Threshold: 7 (scores below 7 indicate issues)
- Format: Multi-turn evaluation (entire conversation analyzed)

### 3.7 Output Files for Conversation Evaluation

```
conversation_generator/personas/personas_20251209_140611/conversations_20251209_141530/
├── {conversation-id-1}.json                                      # Individual conversations
├── {conversation-id-2}.json
├── ...
├── _metadata.json                                                # Generation metadata
├── cxa_evals_multi_turn_conversations.json                       # CXA Evals format
├── cxa_evals_conversation_generator_custom_config.json           # Evaluation configuration
└── cxa-evals-output/                                             # Evaluation results (after running CXA Evals)
```

---

## 4. CXA Evals Framework Integration

### 4.1 Evaluator Types Used

This project uses the **CustomEvaluator** from the CXA Evals framework with domain-specific rules tailored for persona and conversation generation.

| Evaluator Type | Purpose | Metrics |
|----------------|---------|---------|
| **CustomEvaluator (Persona)** | Evaluate quality of generated personas | 5 custom rules: diversity, completeness, relevance, distribution, count accuracy |
| **CustomEvaluator (Conversation)** | Evaluate quality of customer simulation | 3 custom rules: persona adherence, goal pursuit, complexity appropriateness |

### 4.2 How CXA Evals Works

```mermaid
flowchart LR
    A[Input: CXA JSON] --> B[CXA Evals Framework]
    B --> C[Load Custom Rules Config]
    C --> D[For Each Conversation/Persona]
    D --> E[LLM Evaluator<br/>with Custom Rules]
    E --> F[Score Each Rule<br/>1-10 Scale]
    F --> G[Aggregate Scores]
    G --> H[Generate Report]
    H --> I[Output: JSON Results]
    
    style A fill:#e1f5e1
    style E fill:#e1e5ff
    style I fill:#ffe1e1
```

**Process:**
1. Load the transformed data (CXA Evals format JSON)
2. Load the custom rules configuration
3. For each item (persona or conversation):
   - Apply LLM-based evaluation using custom rules
   - Score each rule on a 1-10 scale
   - Compare against threshold (7)
4. Generate aggregated results and detailed feedback
5. Save results to `cxa-evals-output/` directory

### 4.3 Variable Substitution

CXA Evals supports dynamic variable substitution in rule descriptions:

**Example Rule:**
```json
{
  "rule_name": "persona_adherence",
  "rule_description": "The Customer should communicate with the tone: {{persona_tone}}."
}
```

**At Evaluation Time:**
- `{{persona_tone}}` is replaced with actual value: "disappointed and upset"
- This allows personalized evaluation for each conversation

**Available Variables:**
- **Persona Eval:** `{{persona_prompt}}`, `{{num_personas_generated}}`
- **Conversation Eval:** `{{persona_name}}`, `{{persona_description}}`, `{{persona_goal}}`, `{{persona_tone}}`, `{{persona_complexity}}`

---

## 5. Improvement Recommendations Based on Eval Results

### 5.1 Interpreting Evaluation Results

**Score Ranges:**
- **9-10:** Excellent - Meets or exceeds expectations
- **7-8:** Good - Meets minimum quality standards
- **5-6:** Fair - Needs improvement
- **1-4:** Poor - Significant issues

### 5.2 Persona Generation Improvements

| Issue Identified | Eval Score | Recommended Action |
|------------------|------------|-------------------|
| **Low diversity (≤6)** | persona_diversity | Refine prompt to explicitly request different tones, complexity levels, and situations. Example: "Include 3 simple, 4 medium, and 3 complex personas" |
| **Missing fields (≤6)** | persona_completeness | Check system prompt clarity. May indicate LLM hallucination or JSON parsing issues. Consider using stricter JSON schema validation. |
| **Irrelevant personas (≤6)** | persona_relevance | Make the prompt more specific about the business domain and customer scenarios. Add concrete examples. |
| **Wrong distribution (≤6)** | persona_distribution | Use explicit percentages in prompt: "50% calm, 30% frustrated, 20% confused" instead of vague descriptions. |
| **Wrong count (≤6)** | persona_count_accuracy | Ensure prompt clearly states number. Check for prompt requesting >50 personas (should return empty list). |

**Example Improved Prompt:**
```
Generate exactly 10 customer personas for a flower delivery company like 1800flowers.com.

Distribution requirements:
- 5 personas: calm and polite tone (complexity: simple or medium)
- 5 personas: frustrated or disappointed tone (complexity: medium or complex)

Scenario types to include:
- 2 personas: delivery timing issues
- 2 personas: quality problems (wilted/damaged flowers)
- 2 personas: order modifications or cancellations
- 2 personas: general inquiries (pricing, products, occasions)
- 2 personas: special requests (custom arrangements, subscriptions)
```

### 5.3 Conversation Generation Improvements

| Issue Identified | Eval Score | Recommended Action |
|------------------|------------|-------------------|
| **Persona drift (≤6)** | persona_adherence | Strengthen persona prompts with more specific behavioral traits. Add explicit reminders in customer agent's system prompt. Increase context window to maintain full conversation history. |
| **Goal not pursued (≤6)** | goal_pursuit | Make persona goals more concrete and measurable. Example: Instead of "get help", use "get a full refund within 3 business days". |
| **Wrong complexity (≤6)** | complexity_appropriate | Define complexity more clearly in persona descriptions. Simple: 1-2 questions. Medium: Follow-ups, some negotiation. Complex: Multiple issues, emotional, escalation potential. |
| **Unnatural conversations** | Overall | Increase temperature slightly (0.7 → 0.8) for more variety. Review knowledge base for completeness - gaps force CSR to escalate unnecessarily. |
| **Too many escalations** | Overall | Expand knowledge base coverage. Review escalation keywords - may be too sensitive. Train CSR agent to handle edge cases better. |

**Example Persona Improvement:**

**Before (Vague):**
```json
{
  "name": "Upset Customer",
  "description": "Customer is not happy",
  "goal": "Fix the problem",
  "tone": "angry",
  "complexity": "medium"
}
```

**After (Specific):**
```json
{
  "name": "Angry Late Delivery Customer",
  "description": "Customer ordered anniversary flowers for today, but delivery is now 2 hours late and the restaurant reservation is in 30 minutes. They've called twice already with no update.",
  "goal": "Get immediate delivery or a full refund plus compensation for the ruined evening",
  "tone": "angry and demanding, but not abusive",
  "complexity": "complex"
}
```

### 5.4 Knowledge Base Improvements

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Insufficient Coverage** | High escalation rate (>40%) | Add more FAQ categories. Review actual customer questions from transcripts. Cover edge cases. |
| **Vague Answers** | CSR gives generic responses | Make knowledge base answers more specific. Include exact numbers, timeframes, and procedures. |
| **Outdated Information** | CSR provides incorrect info | Regular reviews and updates. Add version/date to knowledge base. |
| **No Escalation Path** | CSR invents policies | Add explicit guidance on when to escalate and how to phrase the transfer. |

### 5.5 Model Configuration Tuning

| Parameter | Current Default | When to Increase | When to Decrease |
|-----------|-----------------|------------------|------------------|
| **Temperature** | 0.7 | Conversations feel repetitive or robotic | Responses are too random or off-topic |
| **Max Tokens** | 500 | Responses are cut off mid-sentence | Want more concise responses |
| **Max Turns** | 20 | Many conversations hit the limit | Conversations feel too long |

### 5.6 Iterative Improvement Process

```mermaid
flowchart LR
    A[Generate Personas] --> B[Run Persona Evals]
    B --> C{Scores ≥7?}
    C -->|No| D[Refine Prompt]
    D --> A
    C -->|Yes| E[Generate Conversations]
    E --> F[Run Conversation Evals]
    F --> G{Scores ≥7?}
    G -->|No| H[Improve Personas<br/>or Knowledge Base]
    H --> E
    G -->|Yes| I[Production Ready]
    
    style I fill:#90EE90
```

**Recommended Workflow:**
1. **Week 1:** Generate initial personas → Evaluate → Refine prompt based on results
2. **Week 2:** Generate conversations → Evaluate → Identify knowledge base gaps
3. **Week 3:** Expand knowledge base → Re-generate conversations → Evaluate
4. **Week 4:** Fine-tune model parameters → Final validation
5. **Ongoing:** Monitor eval scores, maintain knowledge base, update personas for new scenarios

---

## 6. Output Structure and File Organization

### 6.1 Complete Directory Structure

```
conversation_generator/personas/personas_20251209_140611/
│
├── personas.json                                       # Generated personas with embedded metadata
├── _metadata.json                                      # Metadata (backward compatibility)
│
├── cxa_evals_personas.json                             # Personas in CXA Evals format
├── cxa_evals_persona_generator_custom_config.json      # Evaluation config for personas
└── cxa-evals-output/                                   # Persona evaluation results
    └── evaluation_results_20251209_140615.json
│
└── conversations_20251209_141530/
    ├── {uuid-1}.json                                   # Individual conversation files
    ├── {uuid-2}.json
    ├── {uuid-3}.json
    ├── ...
    ├── _metadata.json                                  # Conversation generation metadata
    │
    ├── cxa_evals_multi_turn_conversations.json         # Conversations in CXA Evals format
    ├── cxa_evals_conversation_generator_custom_config.json  # Evaluation config
    └── cxa-evals-output/                               # Conversation evaluation results
        └── evaluation_results_20251209_141545.json
```

### 6.2 Traceability

Each output is traceable through timestamps and metadata:
- **Personas timestamp:** `20251209_140611` - When personas were generated
- **Conversations timestamp:** `20251209_141530` - When conversations were generated
- **Metadata files:** Link conversations back to their source personas
- **Evaluation configs:** Reference correct data files with relative paths

---

## 7. Key Metrics and Success Criteria

### 7.1 Quality Metrics

| Metric | Target | Good | Needs Improvement |
|--------|--------|------|-------------------|
| **Persona Diversity Score** | ≥8 | ≥7 | <7 |
| **Persona Completeness** | 10 | ≥9 | <9 |
| **Persona Relevance** | ≥8 | ≥7 | <7 |
| **Persona Distribution** | ≥9 | ≥8 | <8 |
| **Persona Count Accuracy** | 10 | 10 | <10 |
| **Persona Adherence** | ≥8 | ≥7 | <7 |
| **Goal Pursuit** | ≥8 | ≥7 | <7 |
| **Complexity Appropriate** | ≥8 | ≥7 | <7 |

### 7.2 Operational Metrics

| Metric | Target |
|--------|--------|
| **Conversation Resolution Rate** | >60% resolved, <30% escalated |
| **Average Turn Count** | 6-12 turns |
| **Error Rate** | <5% failed conversations |
| **Generation Time** | <30 seconds per conversation |

---

## 8. Frequently Asked Questions

### Q: How long does the entire process take?

**A:** Timing breakdown:
- Persona generation: ~30-60 seconds (depends on number of personas)
- Conversation generation: ~20-30 seconds per conversation
- CXA Evals: ~5-10 minutes for 10 conversations

**Example:** 10 personas + 10 conversations + evals = ~15-20 minutes total

### Q: Can I use different LLM models for different agents?

**A:** Yes! The configuration allows separate deployments:
- `customer_deployment`: Model for customer agent (default: gpt-4o-mini)
- `csr_deployment`: Model for CSR agent (default: gpt-4o-mini)

You can use GPT-4 for more complex personas or GPT-3.5 for cost savings.

### Q: What if my knowledge base is incomplete?

**A:** Start with the generic FAQ and iterate:
1. Generate conversations with generic knowledge base
2. Review which queries lead to escalation
3. Add specific FAQs for those scenarios
4. Re-generate and evaluate

### Q: How do I know if my personas are good enough?

**A:** Check these indicators:
- Persona evaluation scores all ≥7
- Distribution matches your prompt (check `persona_distribution` score)
- Variety in tones, complexity levels, and goals
- Relevance to your specific business domain

### Q: Can I evaluate the CSR agent's performance?

**A:** The current custom rules focus on Customer agent adherence to personas. To evaluate CSR performance, you would need to create additional custom rules such as:
- Knowledge base usage accuracy
- Empathy and professionalism
- Resolution efficiency
- Escalation appropriateness

---

## 9. Next Steps

### For Product Teams
1. **Review** this presentation and provide feedback on evaluation criteria
2. **Define** business-specific success metrics and thresholds
3. **Validate** that custom rules align with product quality goals
4. **Plan** integration with existing quality assurance workflows

### For Implementation
1. **Set up** Azure OpenAI credentials and deployments
2. **Create** domain-specific knowledge bases
3. **Generate** initial persona sets for key customer scenarios
4. **Run** evaluation pipeline and establish baseline metrics
5. **Iterate** based on evaluation feedback

### For Continuous Improvement
1. **Monitor** evaluation scores over time
2. **Expand** knowledge base based on real customer interactions
3. **Refine** persona prompts to cover emerging scenarios
4. **Update** custom rules as product requirements evolve

---

## Appendix A: Configuration Reference

### Persona Generator Configuration
- `--prompt`: Natural language scenario description
- `--temperature`: LLM temperature (default: 0.7)
- `--model`: Azure OpenAI deployment name

### Conversation Generator Configuration
```json
{
  "azure_openai_api_key": "your-key",
  "azure_openai_endpoint": "https://your-resource.cognitiveservices.azure.com/",
  "customer_deployment": "gpt-4o-mini",
  "csr_deployment": "gpt-4o-mini",
  "max_turns": 20,
  "temperature": 0.7,
  "max_tokens": 500,
  "knowledge_base_path": "conversation_generator/knowledge_base/",
  "persona_templates_path": "conversation_generator/personas/personas_20251209_140611/personas.json"
}
```

### CXA Evals Configuration
- `lower_bound_score`: 1
- `upper_bound_score`: 10
- `score_threshold`: 7
- `turn_mode`: "single_turn" (personas) or "multi_turn" (conversations)

---

## Appendix B: Example Commands

### Generate Personas
```bash
python generate_personas.py --prompt "Generate 10 customer personas for a flower delivery company with 50% calm and 50% frustrated customers"
```

### Generate Conversations
```bash
# Update config.json with persona path first
python generate_conversations.py
```

### Run CXA Evals
```bash
# Navigate to the output directory
cd conversation_generator/personas/personas_20251209_140611/

# Run persona evaluation using CXA Evals framework with:
# - cxa_evals_personas.json (input data)
# - cxa_evals_persona_generator_custom_config.json (evaluation rules)

# Navigate to conversations directory
cd conversations_20251209_141530/

# Run conversation evaluation using CXA Evals framework with:
# - cxa_evals_multi_turn_conversations.json (input data)
# - cxa_evals_conversation_generator_custom_config.json (evaluation rules)
```

---

## Document Version
- **Version:** 1.0
- **Date:** December 10, 2025
- **Author:** SimulationAgent Evals Team
- **Status:** Product Presentation Ready

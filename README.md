# 🧠 Agentic Dataset Reasoning Chatbot

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Frontend](https://img.shields.io/badge/Frontend-Custom_UI-blue)
![Claude](https://img.shields.io/badge/LLM-Claude%20Sonnet%204-purple)
![Version](https://img.shields.io/badge/version-v5.0-orange)

---

# 🚀 Overview

This repository contains multiple versions of an **Agentic Dataset Reasoning Chatbot** that enables users to interact with structured datasets using natural language.

The project demonstrates the evolution from a:

```text
Rule-Based Chatbot
        ↓
Agentic Dataset Assistant
        ↓
Reasoning Agent
        ↓
Structured Dataset Reasoning Engine
        ↓
Briefing-Aware Contextual Reasoning Engine
```

The system combines:

- Deterministic dataset analytics
- Conversational memory
- LLM reasoning
- Agentic planning & execution
- Structured query planning
- Dynamic filtering & sorting
- Briefing-rule-aware exclusion reasoning
- Modular AI architecture

to build intelligent analytical assistants capable of reasoning over structured datasets.

---

# 📚 Project Versions

## 🔹 Chatbot_V1.0_RuleBased

The first implementation based entirely on rule-based logic.

**Features**
- Rule-based query parsing
- Dataset schema interpretation
- Section detection
- Ranking analysis
- Direct dataset lookup

**Limitations**
- No reasoning capability
- Hard-coded query handling
- Limited conversational flexibility

---

## 🔹 Chatbot_V2.0_Agentic

Introduced the first agent-based architecture combining deterministic tools with LLM reasoning.

**Features**
- Agent-based chatbot architecture
- QueryEngine for deterministic dataset querying
- Gemini-powered reasoning layer
- Section-aware dataset retrieval
- Conversation memory
- Interactive Streamlit interface

**Improvements over V1**
- More flexible natural language understanding
- Modular architecture
- Separation between reasoning and dataset tools

---

## 🔹 Chatbot_V3.0_AgenticReasoning

Introduced structured reasoning and planning pipelines.

**Features**
- Planner → Executor reasoning pipeline
- Tool-based dataset interaction
- Ranking explanation capability
- Conversational memory
- Multi-turn dataset exploration

**Improvements over V2**
- Structured planning architecture
- Improved reasoning capability
- Better explainability
- Multi-step analytical workflows

---

## 🔹 Chatbot_V4.0_AgenticReasoningEngine

Introduced a **Structured Dataset Reasoning Engine** — transitioning from an LLM-centric chatbot to an LLM-guided deterministic execution engine.

The LLM now handles planning, intent understanding, and fallback reasoning while deterministic Python handles filtering, sorting, ranking, and dataset analytics.

**Features**
- Claude Sonnet 4 integration
- Structured query planning
- Generic filtering engine
- Dynamic executor routing
- Deterministic analytical execution
- Token usage monitoring
- Custom modern frontend

**Pipeline**

```text
User Question → Frontend → FastAPI → ChatbotAgent
      → Planner → Query Plan → Executor
      → QueryEngine → Deterministic Logic → Response
```

**Improvements over V3**
- Structured executable query planning
- Dynamic filtering architecture
- Generic analytical execution engine
- Reduced token usage
- Modern frontend redesign
- Lower hallucination rate

---

## 🔹 Chatbot_V5.0_ContextualReasoningEngine

Introduced **briefing-rule-aware reasoning** — the system now understands *why* placement decisions were made in the context of actual client briefing rules, not just the dataset.

**What's new**
- `section_prompts.json` support — client briefing rules loaded at startup
- Section coverage validation — warns on mismatches between dataset sections and JSON keys
- Enriched exclusion cards:
  - Colour-coded relevance badge (High / Medium / Low / Not Relevant)
  - AI-generated reason specific to the article
  - Key article text that triggered the evaluation
  - Briefing rule bullets with `→` redirects highlighted
- Pretty section names (`aged_and_community_care` → `Aged and Community Care`)
- Formatted dates (ISO → `3 Feb 2026`) and clean integer ranks (`9.0` → `9`)
- XLSX dataset support alongside CSV
- Unselected item placement fallback
- Ranking why-questions now correctly return `Ordering_Reason`

**Improvements over V4**
- Reasoning grounded in actual client briefing rules
- Richer, more readable exclusion explanations
- Startup validation catches JSON/dataset mismatches early
- Cleaner display formatting throughout

---

# 🗂 Project Structure

```text
Chatbot
│
├── Chatbot_V1.0_RuleBased
│
├── Chatbot_V2.0_Agentic
│
├── Chatbot_V3.0_AgenticReasoning
│
├── Chatbot_V4.0_AgenticReasoningEngine
│
├── Chatbot_V5.0_ContextualReasoningEngine
│   ├── chatbot
│   │   ├── agent.py
│   │   ├── planner.py
│   │   ├── executer.py
│   │   ├── query_engine.py
│   │   ├── retriever.py
│   │   ├── generator.py
│   │   ├── memory.py
│   │   └── dataset.py
│   │
│   ├── schema
│   │   └── models.py
│   │
│   ├── Data
│   │   ├── Full_Enriched_Dataset.csv
│   │   └── section_prompts.json
│   │
│   ├── frontend
│   │   ├── index.html
│   │   ├── app.js
│   │   └── style.css
│   │
│   ├── src
│   │   ├── main.py
│   │   └── ui.py
│   │
│   ├── .env
│   └── README.md
│
└── README.md
```

---

# ⚙️ Technology Stack

**Core**
- Python 3.10+
- FastAPI
- Pandas / openpyxl
- HTML / CSS / Vanilla JavaScript

**LLM Providers**
- V2–V3 → Google Gemini API
- V4–V5 → Anthropic Claude Sonnet 4

**User Interfaces**
- V2–V3 → Streamlit
- V4–V5 → Custom Frontend UI

---

# 🔮 Future Improvements

- LLM-synthesised briefing rule explanations (fuse rule + reason into one readable sentence)
- Multi-step reasoning chains
- Autonomous query decomposition
- Semantic vector retrieval
- Hybrid RAG pipelines
- Multi-dataset support
- Streaming responses
- Visualization dashboards
- Evaluation benchmarks

---

# 🎯 Goal

To explore how AI agents can interact with structured datasets by combining deterministic dataset tools, LLM reasoning, structured execution pipelines, and agentic planning systems — building intelligent analytical assistants capable of advanced, explainable dataset reasoning.

---

# 👨‍💻 Author

**Muhammad Huzaifa**

---

# ⭐ If you like this project, consider starring the repository!
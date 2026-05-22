# 🧠 Agentic Dataset Reasoning Engine (V5.0)

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Frontend](https://img.shields.io/badge/Custom%20Frontend-JS%20%2B%20HTML-blue)
![Claude](https://img.shields.io/badge/LLM-Claude%20Sonnet%204-purple)
![Version](https://img.shields.io/badge/version-v5.0-orange)

---

# 🚀 Overview

An advanced **Agentic AI-powered Dataset Reasoning Engine** that enables users to interact with structured news/media datasets using natural language.

The system combines:

- Structured query planning
- Deterministic dataset analytics
- Conversational memory
- Agentic reasoning
- Dynamic execution pipelines
- LLM-guided orchestration
- **Briefing-rule-aware section reasoning** *(new in V5)*

to answer analytical and reasoning-based questions about:

- News articles
- Rankings
- Sections
- Placement reasoning
- Dataset metadata
- Selection and exclusion explanations

---

# ⚡ Reasoning Pipeline

```text
User Question
      ↓
Frontend UI
      ↓
FastAPI Backend
      ↓
ChatbotAgent
      ↓
Planner
      ↓
Structured Query Plan
      ↓
Executor
      ↓
Query Engine
      ↓
Deterministic Dataset Logic
      ↓
Formatted Response
```

---

# 🧩 Core Modules

### 🧠 Planner

Converts natural language into structured executable query plans.

Example:

```json
{
  "operation": "filter_items",
  "filters": [
    {
      "field": "wordCount",
      "operator": ">",
      "value": 800
    }
  ],
  "sort_by": "wordCount",
  "limit": 10
}
```

---

### ⚙️ Executor

Routes structured operations to the correct analytical engine.

---

### 📊 QueryEngine

Handles deterministic dataset analytics including:

- Filtering and sorting
- Ranking lookups
- Section analytics
- Item reasoning
- Enriched section exclusion reasoning *(returns relevance, relevant text, and section context)*

---

### 📦 DataRetriever

Fetches relevant dataset rows for reasoning and explanations.

---

### ✨ AnswerGenerator

Claude-based fallback reasoning layer used only when deterministic execution is insufficient.

---

### 💬 ConversationMemory

Maintains conversational context and supports reference resolution across queries.

---

### 📋 DatasetManager *(updated in V5)*

- Auto-detects sections from `_answer` columns
- Supports both `.csv` and `.xlsx` datasets
- Loads and validates `section_prompts.json` briefing rules at startup
- Runs a coverage check comparing dataset sections against JSON keys — warns on mismatches in both directions

---

# 🖥️ Frontend

A fully custom-built frontend interface featuring:

- ChatGPT-style UI
- Sidebar with recent chats
- Real-time responses
- Stop generation button
- Smooth scrolling
- Modern dark theme
- Dynamic empty state
- Responsive chat layout

---

# 📁 Project Structure

```text
Chatbot_V5.0_BriefingAwareReasoning
│
├── Data
│   ├── Full_Enriched_Dataset.csv
│   └── section_prompts.json          ← briefing rules (new in V5)
│
├── chatbot
│   ├── agent.py
│   ├── dataset.py
│   ├── query_engine.py
│   ├── retriever.py
│   ├── generator.py
│   ├── memory.py
│   ├── planner.py
│   └── executer.py
│
├── schema
│   └── models.py
│
├── src
│   ├── main.py
│   └── ui.py
│
├── frontend
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── .env
├── .gitignore
└── README.md
```

---

# ✨ Key Features

### 🏆 Ranking Analytics

- Highest and lowest ranked items
- Top ranked articles
- Section-level ranking

```text
List top ranked items in Road Safety
```

---

### ⚡ Dynamic Filtering Engine

Supports structured filtering and sorting using natural language.

```text
Find articles with word count above 800
Find articles containing Operation Nexus
```

Capabilities:
- Numeric and text filtering
- Dynamic sorting
- Section-aware querying
- Result limiting

---

### 📍 Item Placement Analysis

```text
Where was item R00131337085 placed?
```

Correctly handles both placed and unselected items — falls back to logical section detection when `Ordering_Section` is unpopulated.

---

### 🧠 Selection & Exclusion Reasoning *(enhanced in V5)*

Explains why items were selected, ranked, rejected, or placed in specific sections.

```text
Why was it placed there?
Why was it ranked 3rd?
Why was it unselected?
Why wasn't it placed in any other section?
```

V5 enriches exclusion answers with:

- **Relevance badge** — colour-coded High / Medium / Low / Not Relevant
- **AI reason** — specific explanation for that article
- **Key article text** — the excerpt that triggered the evaluation
- **Briefing rule** — the exact "Do not include" rules for that section, rendered as clean bullet points with `→` redirects highlighted

---

### 📋 Briefing-Rule-Aware Reasoning *(new in V5)*

Each dataset now ships with a `section_prompts.json` file defining the inclusion and exclusion rules for every section. At startup the system:

1. Loads the rules
2. Validates coverage — warns if any dataset section is missing a rule or if the JSON contains keys not present in the dataset
3. Attaches the relevant rule block to every exclusion card at query time

Example startup output:

```text
── Section Prompt Coverage ──────────────────
  ✔  Matched  (5): ['accidents', 'corporate', 'road_safety', 'social_insurance', 'victorian_government']
─────────────────────────────────────────────
```

---

### 💬 Conversational Memory

Supports context-aware follow-up questions.

```text
Tell me about R00131337085
Where was it placed?
Why was it unselected?
Why wasn't it placed in Road Safety?
```

---

# 🔄 What Changed in V5

| Area | V4 | V5 |
|---|---|---|
| `dataset.py` | CSV only | CSV + XLSX, loads `section_prompts.json`, coverage validation |
| `query_engine.py` | Returns plain reason tuples | Returns enriched dicts with reason, relevance, relevant text |
| `agent.py` | Raw section slug display, raw ISO dates, float ranks | Pretty section names, formatted dates, clean ranks, briefing rule cards |
| `main.py` | `GEMINI_API_KEY` | `ANTHROPIC_API_KEY`, `SECTION_PROMPTS_PATH` wired in |
| `Data/` | CSV only | + `section_prompts.json` |

---

# ⚙️ Requirements

- Python 3.10+

```bash
pip install fastapi uvicorn pandas openpyxl python-dotenv anthropic
```

---

# 🔐 Environment Setup

```env
ANTHROPIC_API_KEY=your_api_key_here
```

---

# ▶️ Running the Application

### 1️⃣ Start Backend

```bash
uvicorn src.main:app --reload --port 8001
```

### 2️⃣ Open Frontend

```text
frontend/index.html
```

---

# 🌐 Access

- API Docs → http://127.0.0.1:8001/docs
- Chat UI → frontend/index.html

---

# 🧱 Tech Stack

- FastAPI
- Anthropic Claude Sonnet 4
- Vanilla JavaScript
- HTML / CSS
- Pandas
- Python

---

# 📜 Version History

## 🔹 V1.0 — Rule-Based System
- Deterministic dataset querying, no reasoning

## 🔹 V2.0 — Agentic Foundation
- Modular architecture, initial LLM integration

## 🔹 V3.0 — Reasoning Agent
- Planner → Executor pipeline, conversational memory, multi-step analytical reasoning

## 🔹 V3.1 — Custom Frontend Upgrade
- Full frontend redesign, chat-based interaction, sidebar history, stop-generation controls

## 🔹 V4.0 — Structured Agentic Reasoning Engine
- Claude Sonnet integration, structured query planning, generic filtering engine, dynamic executor routing, deterministic analytical execution, reduced token usage, token monitoring

## 🔹 V5.0 — Briefing-Aware Reasoning Engine
- `section_prompts.json` support — briefing rules loaded and validated at startup
- Section coverage check with mismatch warnings
- Enriched exclusion cards: relevance badge, AI reason, article key text, briefing rule bullets
- Pretty section names, formatted dates, clean integer ranks
- XLSX dataset support
- Unselected item placement fallback
- Fixed env var (`ANTHROPIC_API_KEY`)

---

# 🔮 Future Improvements

- LLM-synthesised briefing rule explanations (fuse rule + reason into one readable sentence)
- Multi-step reasoning chains
- Semantic vector retrieval
- Hybrid RAG pipelines
- Multi-dataset support
- Streaming responses
- Visualization dashboards
- Evaluation benchmarks

---

# 👤 Author

Muhammad Huzaifa

---

# ⭐ If you like this project, consider starring it!
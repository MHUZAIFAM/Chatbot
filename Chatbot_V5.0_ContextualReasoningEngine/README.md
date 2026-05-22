# 🧠 Agentic Dataset Reasoning Engine (V4.0)

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Frontend](https://img.shields.io/badge/Custom%20Frontend-JS%20%2B%20HTML-blue)
![Claude](https://img.shields.io/badge/LLM-Claude%20Sonnet%204-purple)
![Version](https://img.shields.io/badge/version-v4.0-orange)

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

to answer analytical and reasoning-based questions about:

- News articles
- Rankings
- Sections
- Placement reasoning
- Dataset metadata
- Selection explanations

---

# ⚡ Structured Agentic Querying (V4)

The system now follows a modular reasoning pipeline:

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

- Filtering
- Sorting
- Ranking
- Counting
- Section analytics
- Item reasoning
- Dynamic querying

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
Chatbot_V4.0_AgenticReasoningEngine
│
├── Data
│   └── Full_Enriched_Dataset.csv
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

# 📊 Dataset Exploration

- Count total items
- Count total sections
- Count items per section
- Count ranked/unranked items

Example:

```text
How many items are there in this dataset?
```

---

# 🧾 Section Analysis

- List all items inside a section
- Count items in a section
- Compare sections
- Identify sections with most items
- Section ranking analytics

Example:

```text
Which section has the highest number of articles?
```

---

# 🏆 Ranking Analytics

- Highest ranked items
- Lowest ranked items
- Top ranked articles
- Ranked item listings
- Average rank per section

Example:

```text
List top ranked items in Health Funds
```

---

# ⚡ Dynamic Filtering Engine (NEW)

Supports structured filtering and sorting using natural language.

Examples:

```text
Find articles with word count above 800
```

```text
Find healthcare articles with score above 0.8
```

```text
Find articles containing diabetes
```

Capabilities include:

- Numeric filtering
- Text filtering
- Dynamic sorting
- Section-aware querying
- Result limiting

---

# 📍 Item Placement Analysis

Example:

```text
Where was item 1167981127 placed?
```

Output:

```text
Item 1167981127 was placed in Calvary Coverage
```

---

# 🧠 Selection Reasoning

Explains WHY items were:

- Selected
- Ranked
- Rejected
- Placed in specific sections

Example:

```text
Why was item 1167981127 placed there?
```

---

# 💬 Conversational Memory

Supports context-aware follow-up questions.

Examples:

```text
Where was it placed?
Why was it ranked there?
Tell me more about that item.
```

---

# 🚀 Token Optimization (V4)

V4 dramatically reduces token usage by shifting analytical logic from the LLM to deterministic Python execution.

## Previous Architecture (V3)

```text
Entire Dataset → LLM → Answer
```

## New Architecture (V4)

```text
Planner → Python Execution → Structured Response
```

Benefits:

- Lower API costs
- Faster responses
- Higher accuracy
- Reduced hallucinations
- Better scalability

---

# 📈 Token Usage Monitoring

The system now tracks:

- Planner token usage
- Generator token usage

allowing detailed performance analysis and optimization.

---

# ⚙️ Requirements

- Python 3.10+

Install dependencies:

```bash
pip install fastapi uvicorn pandas python-dotenv anthropic
```

---

# 🔐 Environment Setup

Create a `.env` file:

```env
ANTHROPIC_API_KEY=your_api_key_here
```

---

# ▶️ Running the Application

## 1️⃣ Start Backend

```bash
uvicorn src.main:app --reload --port 8001
```

---

## 2️⃣ Run Frontend

Open manually:

```text
frontend/index.html
```

OR serve locally:

```bash
python -m http.server
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
- HTML/CSS
- Pandas
- Python

---

# 📜 Version History

## 🔹 V1.0 — Rule-Based System

- Deterministic dataset querying
- No reasoning

---

## 🔹 V2.0 — Agentic Foundation

- Modular architecture
- Initial LLM integration

---

## 🔹 V3.0 — Reasoning Agent

- Planner → Executor pipeline
- Conversational memory
- Multi-step analytical reasoning

---

## 🔹 V3.1 — Custom Frontend Upgrade

- Full frontend redesign
- Chat-based interaction system
- Sidebar history
- Stop-generation controls

---

## 🔹 V4.0 — Structured Agentic Reasoning Engine

- Claude Sonnet integration
- Structured query planning
- Generic filtering engine
- Dynamic executor routing
- Deterministic analytical execution
- Reduced token usage
- Structured filtering/sorting
- Improved conversational reasoning
- Token monitoring system

---

# 🔮 Future Improvements

- Multi-step reasoning chains
- Semantic vector retrieval
- Hybrid RAG pipelines
- Multi-dataset support
- Streaming responses
- Visualization dashboards
- Evaluation benchmarks
- Autonomous query decomposition

---

# 👤 Author

Muhammad Huzaifa

---

# ⭐ If you like this project, consider starring it!
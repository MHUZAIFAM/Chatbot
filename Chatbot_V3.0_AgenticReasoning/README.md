# 🧠 Agentic News Dataset Chatbot

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Frontend](https://img.shields.io/badge/Custom%20Frontend-JS%20%2B%20HTML-blue)
![Version](https://img.shields.io/badge/version-v3.1-orange)

---

## 🚀 Overview

An **Agentic AI-powered chatbot** that enables users to interact with a structured news dataset using natural language.

This system combines:

* Deterministic dataset analytics
* Conversational memory
* LLM-based reasoning
* Agent planning & execution
* Structured data retrieval

to answer analytical queries about:

* News articles
* Rankings
* Sections
* Placement reasoning

---

## 🧩 Agentic Reasoning Architecture (V3)

The system follows a **Planner → Executor → Reasoning pipeline**:

```
User → Frontend UI → FastAPI → ChatbotAgent
```

### Core Modules

* **Planner** → Converts natural language into structured operations
* **Executor** → Runs deterministic dataset logic
* **QueryEngine** → Handles dataset analytics
* **DataRetriever** → Fetches relevant dataset rows
* **AnswerGenerator** → Generates explanations using Gemini
* **ConversationMemory** → Maintains context across queries

---

## 🖥️ Frontend (New)

A **custom-built chat UI** replaces Streamlit for a more modern experience:

* ChatGPT-style interface
* Sidebar with recent chats
* Real-time responses
* Stop generation button
* Clean dark UI with custom styling

---

## 📁 Project Structure

```
Chatbot_V3.0_AgenticReasoning
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
│   └── main.py
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

## ✨ Key Features

### 📊 Dataset Exploration

* How many items are in the dataset?
* What sections exist?
* Count items per section

---

### 🧾 Section Analysis

* List all items in a section
* Count ranked/unranked items
* Compare sections

---

### 🏆 Ranking Analysis

* Highest/lowest ranked items
* Section-wise rankings
* Ranked item listings

---

### 📍 Item Placement Analysis

Example:

> Where was item 1167981127 placed?

Output:

> Item 1167981127 was placed in *Calvary Coverage*

---

### 🧠 Selection Reasoning

Explain **why items were selected or rejected** using dataset reasoning columns.

---

### 💬 Conversational Memory

Supports context-aware queries:

* "this section"
* "those items"
* "why was it placed here?"

---

## ⚙️ Requirements

* Python **3.10+**

Install dependencies:

```bash
pip install fastapi uvicorn pandas python-dotenv google-generativeai
```

---

## 🔐 Environment Setup

Create a `.env` file:

```env
GEMINI_API_KEY=your_api_key_here
```

---

## ▶️ Running the Application

### 1️⃣ Start Backend

```bash
uvicorn src.main:app --reload --port 8001
```

---

### 2️⃣ Run Frontend

Open manually:

```
frontend/index.html
```

OR serve it:

```bash
python -m http.server
```

---

## 🌐 Access

* API Docs → http://127.0.0.1:8001/docs
* Chat UI → open frontend/index.html

---

## 🧱 Tech Stack

* FastAPI
* Vanilla JS (Frontend)
* HTML/CSS
* Pandas
* Google Gemini API

---

## 📜 Version History

### 🔹 V1.0 — Rule-Based

* Deterministic logic
* No reasoning

---

### 🔹 V2.0 — Agentic

* Modular architecture
* LLM integration

---

### 🔹 V3.0 — Reasoning Agent

* Planner → Executor pipeline
* Multi-step reasoning
* Conversational memory

---

### 🔹 V3.1 — Custom UI Upgrade

* Full frontend redesign
* Chat-based interaction system
* Stop-generation control
* Sidebar chat history

---

## 🔮 Future Improvements

* Vector search (semantic retrieval)
* Multi-dataset support
* Visualization dashboards
* Streaming responses
* Evaluation benchmarks

---

## 👤 Author

Muhammad Huzaifa

---

## ⭐ If you like this project, consider starring it!

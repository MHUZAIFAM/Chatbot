# 🧠 Dataset Analysis Chatbot

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red)
![Version](https://img.shields.io/badge/version-v3.0-orange)


This repository contains multiple versions of a **dataset analysis chatbot** that allows users to interact with structured datasets using natural language queries.

The project demonstrates the evolution from a **rule-based system** to a **fully agentic AI architecture capable of reasoning and planning**.

---

# 📚 Project Versions

## 🔹 Chatbot_V1.0_RuleBased

The **first implementation** of the chatbot based purely on rule-based logic.

### Features

* Rule-based query parsing
* Dataset schema interpretation
* Section detection
* Ranking analysis
* Direct dataset lookup

### Limitations

* No reasoning capability
* Hard-coded query handling
* Limited conversational flexibility

---

## 🔹 Chatbot_V2.0_Agentic

The second version introduces an **agent-based architecture** combining deterministic tools with LLM reasoning.

### Features

* Agent-based chatbot architecture
* Deterministic dataset querying through **QueryEngine**
* Gemini-powered reasoning layer
* Section-aware dataset retrieval
* Conversation memory
* Interactive **Streamlit interface**

### Improvements Over V1

* More flexible natural language queries
* Modular architecture
* Separation between reasoning and dataset tools

---

## 🔹 Chatbot_V3.0_AgenticReasoning

The **most advanced version** of the chatbot implementing **agentic reasoning and planning**.

This version enables the system to **analyze the user query, plan actions, execute dataset tools, and generate explanations**.

### Features

* Agentic reasoning pipeline
* Query planning and execution
* Tool-based dataset interaction
* Structured dataset retrieval
* Ranking explanation capability
* Conversational memory
* Modular reasoning architecture

### Core Components

* **Agent** → Coordinates reasoning
* **Planner** → Decides what actions to take
* **Executer** → Runs dataset tools
* **Retriever** → Retrieves dataset context
* **Generator** → Produces natural language answers
* **Memory** → Maintains conversation context
* **QueryEngine** → Deterministic dataset queries

---

# 🗂 Project Structure

```
Chatbot
│
├── Chatbot_V1.0_RuleBased
│
├── Chatbot_V2.0_Agentic
│
├── Chatbot_V3.0_AgenticReasoning
│   ├── chatbot
│   │   ├── agent.py
│   │   ├── planner.py
│   │   ├── executer.py
│   │   ├── retriever.py
│   │   ├── generator.py
│   │   ├── memory.py
│   │   └── dataset.py
│   │
│   ├── schema
│   │   └── models.py
│   │
│   ├── Data
│   │   └── Full_Enriched_Dataset.csv
│   │
│   └── src
│       ├── main.py
│       └── ui.py
│
└── README.md
```

---

# ⚙️ Technology Stack

* **Python**
* **Streamlit** (UI)
* **Gemini API** (LLM reasoning)
* **Pandas** (dataset processing)
* **Modular agent architecture**

---

# 🚀 Future Improvements

* Fully autonomous agent planning
* Multi-step reasoning chains
* Retrieval-Augmented Generation (RAG)
* Improved ranking explanations
* More advanced dataset analytics
* UI enhancements

---

# 🎯 Goal of the Project

The goal of this project is to explore how **AI agents can interact with structured datasets**, combining:

* deterministic data tools
* reasoning capabilities of LLMs
* conversational interfaces

to build **intelligent analytical assistants**.

---

# 👨‍💻 Author

**Muhammad Huzaifa**

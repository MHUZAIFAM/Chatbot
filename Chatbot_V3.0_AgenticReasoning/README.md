# Agentic News Dataset Chatbot (V3.0)

An **Agentic AI-powered chatbot** that allows users to interact with a
structured news dataset through natural language.

The system combines:

-   deterministic dataset analytics\
-   conversational memory\
-   LLM reasoning\
-   agent planning and execution\
-   structured dataset retrieval

to answer analytical questions about **news articles, rankings,
sections, and placement explanations**.

------------------------------------------------------------------------

# Agentic Reasoning Architecture (V3)

The system follows a **planner → executor → reasoning pipeline**.

User → Streamlit UI → FastAPI Backend → ChatbotAgent

Modules:

-   Planner -- LLM converts question into structured operation\
-   Executor -- executes deterministic dataset operations\
-   QueryEngine -- dataset analytics and computations\
-   DataRetriever -- retrieves relevant dataset rows\
-   AnswerGenerator -- Gemini LLM reasoning\
-   ConversationMemory -- maintains conversation context

------------------------------------------------------------------------

# Project Structure

Chatbot_V3.0_ReasoningAgent

Data/\
Full_Enriched_Dataset.csv

chatbot/\
agent.py\
dataset.py\
query_engine.py\
retriever.py\
generator.py\
memory.py\
planner.py\
executer.py

schema/\
models.py

src/\
main.py\
ui.py

.env\
.gitignore\
README.md

------------------------------------------------------------------------

# Key Features

## Dataset Exploration

Example queries:

How many items are in the dataset?\
What sections exist in the dataset?\
How many items are in each section?

------------------------------------------------------------------------

## Section Analysis

List all items in Calvary Coverage\
How many ranked items are in this section?\
How many unranked items are in each section?

------------------------------------------------------------------------

## Ranking Analysis

Highest ranked item in the dataset\
Lowest ranked item in each section\
List ranked items in Health Care Industry

------------------------------------------------------------------------

## Item Placement Analysis

Where was item 1167981127 placed?

Example output:

Item 1167981127 was placed in the 'Calvary Coverage' section.

------------------------------------------------------------------------

## Selection Reasoning

Why was item 1167634477 unselected?

The system reads dataset \*\_reason columns\* to explain why the item
was excluded from each section.

------------------------------------------------------------------------

## Conversational Memory

Example conversation:

List all items in Calvary Coverage\
How many ranked items are in this section?\
List those ranked items\
Why was item 1167981127 placed here?

The system resolves references such as:

-   this section\
-   those items\
-   why

------------------------------------------------------------------------

# Requirements

Python **3.10+** recommended

Install dependencies:

pip install fastapi uvicorn streamlit pandas python-dotenv
google-generativeai

------------------------------------------------------------------------

# Environment Setup

Create a `.env` file:

GEMINI_API_KEY=your_api_key_here

------------------------------------------------------------------------

# Running the Application

Open two terminals.

Terminal 1:

uvicorn src.main:app --reload --port 8001

Terminal 2:

streamlit run src/ui.py

------------------------------------------------------------------------

# Accessing the Application

Streamlit UI

http://localhost:8501

FastAPI Docs

http://127.0.0.1:8001/docs

Memory Endpoint

http://127.0.0.1:8001/memory

------------------------------------------------------------------------

# Technology Stack

-   FastAPI
-   Streamlit
-   Pandas
-   Google Gemini API
-   Python

------------------------------------------------------------------------

# Version History

## V1.0 --- Rule-Based Chatbot

Chatbot_V1.0_RuleBased

-   Deterministic logic
-   No reasoning
-   No conversational memory

## V2.0 --- Agentic Chatbot

Chatbot_V2.0_Agentic

-   Modular architecture
-   LLM reasoning
-   Structured dataset querying

## V3.0 --- Reasoning Agent

Chatbot_V3.0_ReasoningAgent

New capabilities:

-   Planner → Executor architecture
-   Multi-step reasoning
-   Conversational memory improvements
-   Section-aware dataset analytics
-   Classification explanation generation

------------------------------------------------------------------------

# Future Improvements

-   migrate to google.genai SDK
-   semantic vector search
-   visualization dashboards
-   multi-dataset support
-   reasoning evaluation benchmarks

# Agentic News Dataset Chatbot



An **Agentic AI-powered chatbot** that allows users to interact with a structured news dataset through natural language.



The system combines:


- deterministic data analysis
- conversational memory
- LLM reasoning
- structured dataset retrieval


to answer analytical questions about news articles, rankings, sections, and placement explanations.



The chatbot supports queries such as:



- Which section an item belongs to

- Why an item was not selected

- Highest/lowest ranked items

- Ranked vs unranked items

- Dataset statistics

- Section analytics

- Follow-up conversational questions



---



# Agentic Architecture

The system follows a modular **agent-based architecture**:

```
User
│
▼
Streamlit UI (src/ui.py)
│
▼
FastAPI Backend (src/main.py)
│
▼
ChatbotAgent
├── DatasetManager
├── QueryEngine
│   Deterministic dataset analytics
├── DataRetriever
│   Retrieves relevant dataset rows
├── AnswerGenerator
│   Uses Gemini LLM for reasoning
└── ConversationMemory
    Stores previous interactions
```



This architecture allows the chatbot to combine:



- rule-based reasoning
- structured data querying
- LLM-powered explanations



---



# Project Structure



```

Chatbot\_V2.0\_Agentic

│
├── Data
│   └── Full\_Enriched\_Dataset.csv
│
├── chatbot
│   ├── agent.py              # Main chatbot agent
│   ├── dataset.py            # Dataset loader \& schema detection
│   ├── query\_engine.py       # Deterministic dataset queries
│   ├── retriever.py          # Dataset retrieval layer
│   ├── generator.py          # LLM answer generation
│   ├── memory.py             # Conversation memory
│   ├── planner.py            # Agent planning logic
│   └── executer.py           # Execution logic
│
├── schema
│   └── models.py             # API request/response models
│
├── src
│   ├── main.py               # FastAPI backend
│   └── ui.py                 # Streamlit UI
│
├── .env
├── .gitignore
└── README.md

```



---



# Key Features



## Dataset Exploration



Users can query dataset structure:



- Total number of items
- Number of sections
- Items per section
- Unselected items



Example:



```

How many items are in the dataset?

What sections exist in the dataset?

How many items are in each section?

```



---



## Section Analysis



The chatbot can analyze dataset sections:



```

List all items in Calvary Coverage

How many ranked items are in this section?

What were the unranked items in this section?

```



---



## Ranking Analysis



The system supports ranking queries:



```

Highest ranked item in each section

Lowest ranked item in the dataset

List ranked items in a section

```



---



## Item Placement



Users can inspect where an article was placed.



Example:



```

Where was item 1167981127 placed?

```



Output:



```

Item 1167981127 was placed in the 'Calvary Coverage' section.

```



---



## Selection Explanations



The chatbot can explain **why an item was not selected** in sections.



Example:



```

Why was item 1167634477 unselected?

```



The system reads dataset **_reason columns** and explains exclusion reasons.



---



## Conversational Memory



The chatbot understands follow-up queries:



```

List all items in Calvary Coverage

How many ranked items in this section?

What were those items?

```



The memory system resolves references like:



- this section
- those items
- why



---



# Requirements



Python **3.10+** recommended.



Install dependencies:



```

pip install fastapi uvicorn streamlit pandas python-dotenv google-generativeai

```



---



# Environment Setup



Create a `.env` file:



```

GEMINI_API_KEY=your_api_key_here

```



This key is used by the chatbot for LLM reasoning and explanations.



---



# Running the Application



Open **two terminals**.



### Terminal 1 — Start FastAPI



```

uvicorn src.main:app --reload --port 8001

```



### Terminal 2 — Start Streamlit UI



```

streamlit run src/ui.py

```



---



# Accessing the Application



### Streamlit Chat Interface



```

http://localhost:8501

```



Interactive chatbot interface.



---



### FastAPI Documentation



```

http://127.0.0.1:8001/docs

```



API endpoint testing via Swagger.



---



### Memory Endpoint



```

http://127.0.0.1:8001/memory

```



Displays the chatbot conversation memory.



---



# Technology Stack



- **FastAPI** – backend API

- **Streamlit** – interactive UI

- **Pandas** – dataset processing

- **Google Gemini API** – reasoning & explanations

- **Python** – core system logic



---



# Security



Sensitive credentials are stored in:



```

.env

```



and excluded from version control via:



```

.gitignore

```



---



# Version



This version introduces the **Agentic architecture**, improving:



- modular design

- conversational memory

- reasoning capabilities

- dataset analytics



Previous rule-based implementation is preserved in:



```

Chatbot_V1.0_RuleBased

```




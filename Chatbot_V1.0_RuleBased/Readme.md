# News Dataset Chatbot

A **FastAPI + Streamlit chatbot** that allows users to interact with a structured news dataset.  
The system analyzes dataset sections, item rankings, explanations, sentiment, and metadata using a conversational interface.

The chatbot supports queries such as:

- Item details and placement
- Section counts
- Ranking analysis
- Sentiment analysis
- Section explanations
- Dataset structure queries



# Project Architecture

```
User (Browser)
│
▼
Streamlit UI (src/ui.py)
│
▼
FastAPI Backend (src/main.py)
│
▼
NewsChatbot Engine
(src/chatbot/)
│
▼
Dataset
(Data/Full_Enriched_Dataset.csv)
```

# Project Structure

```
Chatbot V2.1
│
├── Data
│ └── Full_Enriched_Dataset.csv
│
├── src
│ ├── main.py # FastAPI backend
│ ├── ui.py # Streamlit UI
│
│ ├── chatbot
│ │ ├── init.py
│ │ ├── chatbot.py # Core chatbot logic
│ │ ├── data_loader.py
│ │ ├── intents.py
│ │ ├── item_handler.py
│ │ ├── memory.py
│ │ ├── ranking.py
│ │ ├── schema_handler.py
│ │ └── sentiment.py
│
│ └── schema
│ └── models.py # API request/response models
│
├── .env # API keys (not committed)
├── .gitignore
└── README.md
```


# Features

## Dataset Exploration

- List dataset sections
- Count items per section
- Count total items
- Detect unselected items

## Item Analysis

- Retrieve item metadata
- Identify item placement
- Explain why an item belongs to a section

## Ranking System

- Identify highest ranked items
- Identify lowest ranked items

## Sentiment Analysis

Uses **Google Gemini API** to analyze article sentiment.

## Conversation Memory

The chatbot remembers:

- previously referenced items
- previous queries

Accessible via the `/memory` endpoint.


---

# Features

## Dataset Exploration

- List dataset sections
- Count items per section
- Count total items
- Detect unselected items

## Item Analysis

- Retrieve item metadata
- Identify item placement
- Explain why an item belongs to a section

## Ranking System

- Identify highest ranked items
- Identify lowest ranked items

## Sentiment Analysis

Uses **Google Gemini API** to analyze article sentiment.

## Conversation Memory

The chatbot remembers:

- previously referenced items
- previous queries

Accessible via the `/memory` endpoint.

# Requirements

Python **3.10+** recommended.

Install dependencies:

```bash
pip install fastapi uvicorn streamlit pandas python-dotenv google-generativeai
```

# Requirements

Python **3.10+** recommended.

Install dependencies:

```bash
pip install fastapi uvicorn streamlit pandas python-dotenv google-generativeai
```
# Environment Setup

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_api_key_here
```
This key is used for sentiment analysis through the Gemini API.

# Running the Application

- Open two terminals.

## Terminal 1 — Start FastAPI
```uvicorn src.main:app --reload --port 8001```
## Terminal 2 — Start Streamlit UI
```streamlit run src/ui.py```


# Accessing the Application
## Streamlit Interface
```http://localhost:8501```

Interactive chatbot interface.

## FastAPI Documentation
```http://127.0.0.1:8001/docs```

Swagger interface to test API endpoints.

## Memory Endpoint
```http://127.0.0.1:8001/memory```

Returns chatbot memory state.

## Terminal Test
```curl http://127.0.0.1:8001/memory```

# Technology Stack
- FastAPI – backend API
- Streamlit – interactive UI
- Pandas – dataset processing
- Google Gemini API – sentiment analysis
- Python – core logic

# Sensitive credentials are stored in:

`.env`

and excluded from version control via:

`.gitignore`
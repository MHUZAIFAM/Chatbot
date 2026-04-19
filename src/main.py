from fastapi import FastAPI
from src.chatbot.chatbot import NewsChatbot
from src.schema.models import ChatRequest, ChatResponse
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="News Chatbot API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(
    BASE_DIR,
    "..",
    "Data",
    "Full_Enriched_Dataset.csv"
)

# Get API key from environment
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Please add it to your .env file.")

chatbot = NewsChatbot(
    csv_path=csv_path,
    api_key=api_key
)

@app.get("/")
def home():
    return {"status": "API running"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    answer = chatbot.ask(request.question)

    return ChatResponse(answer=answer)

@app.get("/memory")
def get_memory():
    return {
        "item_memory": chatbot.item_memory,
        "general_memory": chatbot.general_memory
    }


# ====================== PROCEDURE ======================
# Open Terminal, Run: uvicorn src.main:app --reload --port 8001
# Open IInd Terminal, Run: streamlit run src/ui.py
# Open Browser,  Run: http://127.0.0.1:8001/docs (For API endpoint chatbot)
#                Run: http://127.0.0.1:8001/memory (For Memory on Browser)
#                Run: curl http://127.0.0.1:8001/memory (On terminal)
#                Run:  http://localhost:8501 (On the browser)
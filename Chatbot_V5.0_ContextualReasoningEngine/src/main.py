import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from chatbot.agent import ChatbotAgent
from schema.models import QuestionRequest, AnswerResponse


# --------------------------------
# Load environment variables
# --------------------------------

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")

DATASET_PATH        = "Data/Full_Enriched_Dataset.csv"
SECTION_PROMPTS_PATH = "Data/section_prompts.json"   # set to None if not used


# --------------------------------
# Initialize FastAPI
# --------------------------------

app = FastAPI(
    title="Agentic News Chatbot",
    version="4.0"
)


# --------------------------------
# CORS (required for frontend)
# --------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------
# Initialize Chatbot Agent
# --------------------------------

chatbot = ChatbotAgent(
    dataset_path=DATASET_PATH,
    api_key=API_KEY,
    section_prompts_path=SECTION_PROMPTS_PATH,
)


# --------------------------------
# Root endpoint
# --------------------------------

@app.get("/")
def root():
    return {"message": "Agentic News Chatbot API is running"}


# --------------------------------
# Ask endpoint
# --------------------------------

@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    answer = chatbot.ask(request.question)
    return AnswerResponse(answer=answer)
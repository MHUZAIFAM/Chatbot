import os
from fastapi import FastAPI
from dotenv import load_dotenv

from chatbot.agent import ChatbotAgent
from schema.models import QuestionRequest, AnswerResponse


# --------------------------------
# Load environment variables
# --------------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

DATASET_PATH = "Data/Full_Enriched_Dataset.csv"


# --------------------------------
# Initialize FastAPI
# --------------------------------
app = FastAPI(
    title="Agentic News Chatbot",
    version="3.0"
)


# --------------------------------
# Initialize Chatbot Agent
# --------------------------------
chatbot = ChatbotAgent(
    dataset_path=DATASET_PATH,
    api_key=API_KEY
)


# --------------------------------
# Root endpoint
# --------------------------------
@app.get("/")
def root():

    return {
        "message": "Agentic News Chatbot API is running"
    }


# --------------------------------
# Ask endpoint
# --------------------------------
@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):

    question = request.question

    answer = chatbot.ask(question)

    return AnswerResponse(answer=answer)
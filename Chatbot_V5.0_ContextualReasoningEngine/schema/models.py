from pydantic import BaseModel


# -----------------------------
# Request Model
# -----------------------------
class QuestionRequest(BaseModel):
    question: str


# -----------------------------
# Response Model
# -----------------------------
class AnswerResponse(BaseModel):
    answer: str
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = "candidate"  # candidate | recruiter


class LoginRequest(BaseModel):
    email: EmailStr
    password: str



class StartInterviewRequest(BaseModel):
    mode: str = "role"  # role | pack
    role: Optional[str] = None
    industry: Optional[str] = "Technology"
    difficulty: Optional[str] = "medium"  # easy | medium | hard
    pack_id: Optional[str] = None
    num_questions: int = 5


class AnswerRequest(BaseModel):
    answer: str


class PackQuestion(BaseModel):
    question: str
    category: str = "technical"
    difficulty: str = "medium"


class PackRequest(BaseModel):
    title: str
    role: str
    industry: str = "Technology"
    description: str = ""
    difficulty: str = "medium"
    questions: List[PackQuestion]

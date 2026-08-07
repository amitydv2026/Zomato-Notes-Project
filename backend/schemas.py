from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, field_validator


# ── User schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty or whitespace-only")
        return v


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Note schemas ──────────────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1)
    tag: Optional[str] = None
    owner_id: int


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    content: Optional[str] = Field(default=None, min_length=1)
    tag: Optional[str] = None


class AISuggestion(BaseModel):
    tags: List[str]
    summary: str


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    tag: Optional[str]
    owner_id: int
    owner_name: Optional[str] = None
    created_at: datetime
    ai_suggestion: Optional[AISuggestion] = None

    model_config = {"from_attributes": True}


# ── Report schemas ────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    id: int
    name: str
    email: EmailStr


class ChatMessage(BaseModel):
    role: str        # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


class UserNoteCount(BaseModel):
    user_id: int
    name: str
    total_notes: int


# ── Search / ranking schemas ──────────────────────────────────────────────────

class ScoredNote(BaseModel):
    id: int
    title: str
    content: str
    tag: Optional[str]
    owner_id: int
    created_at: datetime
    score: Any = None

    model_config = {"from_attributes": True}


class SmartSearchResult(BaseModel):
    id: int
    title: str
    content: str
    tag: Optional[str]
    similarity: float

    model_config = {"from_attributes": True}

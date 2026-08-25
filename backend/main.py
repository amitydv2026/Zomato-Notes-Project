"""
Zomato Notes — FastAPI backend
Implements all endpoints from Parts 1, 2, and 3.
"""

import asyncio
import json
import logging
import os
import time
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import Base, engine, get_db
from algorithms import (
    binary_search_iterative,
    binary_search_recursive,
    insertion_sort_by_key,
    linear_search,
)
from ai_service import get_ai_response, PROMPT_TEMPLATE
from schemas import ChatMessage, ChatRequest
from semantic_search import semantic_search

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Create tables ─────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── App init ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Zomato Notes API",
    description="AI-augmented internal knowledge base for on-call support engineers.",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Base origins always allowed (local dev)
_BASE_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5501",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://127.0.0.1:8001",
    "http://localhost:8001",
]

# ALLOWED_ORIGINS env var lets you add production origins (comma-separated)
# e.g. ALLOWED_ORIGINS=https://yourusername.github.io,https://yourcustomdomain.com
_extra = os.getenv("ALLOWED_ORIGINS", "")
_extra_origins = [o.strip().rstrip("/") for o in _extra.split(",") if o.strip()]

ALLOWED_ORIGINS = _BASE_ORIGINS + _extra_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)


# ── X-Process-Time middleware ─────────────────────────────────────────────────
class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.6f}s"
        return response


app.add_middleware(ProcessTimeMiddleware)


# ── Auth dependency ───────────────────────────────────────────────────────────
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "zomato-secret")


def verify_token(x_token: Optional[str] = Header(default=None)):
    if x_token is None:
        raise HTTPException(status_code=401, detail="Missing x-token header")
    if x_token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid x-token")


# ── Background task helper ────────────────────────────────────────────────────
async def _index_note_background(note_id: int):
    """Simulates a 2–3 second indexing step after note creation."""
    await asyncio.sleep(2.5)
    logger.info(f"[BackgroundTask] Note {note_id} indexed at {time.strftime('%H:%M:%S')}")


@app.get("/ping", tags=["Health"])
def ping():
    """Lightweight keep-alive endpoint. Used by UptimeRobot to prevent Render cold starts."""
    return {"status": "ok"}




@app.post("/users", response_model=schemas.UserResponse, status_code=201, tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create a new user. Email must be unique."""
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    return crud.create_user(db, user)


@app.post("/auth/login", response_model=schemas.LoginResponse, tags=["Auth"])
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Login with email + password. Returns user id, name, email on success."""
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or user.password != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return schemas.LoginResponse(id=user.id, name=user.name, email=user.email)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 — Notes
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/notes", response_model=schemas.NoteResponse, status_code=201, tags=["Notes"])
async def create_note(
    note: schemas.NoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a note. Validates owner_id exists. Fires background indexing task.
    Returns an ai_suggestion field from get_ai_response() (MOCK_AI=1 by default).
    """
    owner = crud.get_user(db, note.owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail=f"User {note.owner_id} not found")

    db_note = crud.create_note(db, note)
    background_tasks.add_task(_index_note_background, db_note.id)

    # AI suggestion
    ai_suggestion = None
    try:
        raw = get_ai_response(db_note.content, PROMPT_TEMPLATE)
        parsed = json.loads(raw)
        ai_suggestion = schemas.AISuggestion(**parsed)
    except Exception as exc:
        logger.warning(f"AI suggestion failed for note {db_note.id}: {exc!r} | raw={locals().get('raw', '')}")

    response = schemas.NoteResponse.model_validate(db_note)
    response.ai_suggestion = ai_suggestion
    response.owner_name = owner.name
    return response


@app.get("/notes", response_model=List[schemas.NoteResponse], tags=["Notes"])
def list_notes(tag: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    """List all notes with owner name. Optional ?tag= filter."""
    notes = crud.get_notes(db, tag)
    # Build owner_id → name map in one query
    user_map = {u.id: u.name for u in db.query(models.User).all()}
    result = []
    for n in notes:
        r = schemas.NoteResponse.model_validate(n)
        r.owner_name = user_map.get(n.owner_id, f"User {n.owner_id}")
        result.append(r)
    return result


@app.get("/notes/search", response_model=List[schemas.ScoredNote], tags=["Notes - Part 2"])
def search_notes(
    keyword: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Ranked search:
    - ?keyword=<value>  → top 5 notes by keyword-occurrence count (insertion sort)
    - ?sort_by=date     → notes sorted descending by creation time (insertion sort)
    """
    notes = crud.get_notes(db)
    note_dicts = [
        {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "tag": n.tag,
            "owner_id": n.owner_id,
            "created_at": n.created_at,
            "created_at_epoch": n.created_at.timestamp() if n.created_at else 0,
        }
        for n in notes
    ]

    if sort_by == "date":
        sorted_notes = insertion_sort_by_key(note_dicts, key="created_at_epoch")
        return sorted_notes

    if keyword:
        kw = keyword.lower()
        for n in note_dicts:
            # Score = occurrences in content + title (title weighted x2)
            content_score = n["content"].lower().count(kw)
            title_score   = n["title"].lower().count(kw) * 2
            n["score"] = content_score + title_score
        sorted_notes = insertion_sort_by_key(note_dicts, key="score")
        # Return only notes with score > 0 (genuine keyword matches)
        matched = [n for n in sorted_notes if n["score"] > 0]
        return matched[:10]

    raise HTTPException(status_code=400, detail="Provide ?keyword= or ?sort_by=date")


@app.get("/notes/lookup", response_model=schemas.NoteResponse, tags=["Notes - Part 2"])
def lookup_note_by_title(
    title: str = Query(..., description="Exact note title"),
    algo: str = Query(default="iterative", pattern="^(iterative|recursive)$"),
    db: Session = Depends(get_db),
):
    """
    Exact-title lookup using binary search.
    The note list is fetched ORDER BY title ASC from the database.
    """
    ordered_notes = crud.get_all_notes_ordered_by_title(db)
    sorted_titles = [n.title for n in ordered_notes]

    if algo == "iterative":
        idx = binary_search_iterative(sorted_titles, title)
    else:
        idx = binary_search_recursive(sorted_titles, title, 0, len(sorted_titles) - 1)

    if idx == -1:
        raise HTTPException(status_code=404, detail=f"Note with title '{title}' not found")

    return ordered_notes[idx]


@app.get("/notes/quick-find", response_model=schemas.NoteResponse, tags=["Notes - Part 2"])
def quick_find_by_tag(
    tag: str = Query(..., description="Tag value to find"),
    db: Session = Depends(get_db),
):
    """Returns the first note with the given tag using linear search."""
    notes = crud.get_notes(db)
    note_dicts = [
        {"id": n.id, "title": n.title, "content": n.content, "tag": n.tag,
         "owner_id": n.owner_id, "created_at": n.created_at}
        for n in notes
    ]
    result = linear_search(note_dicts, key="tag", value=tag)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No note found with tag '{tag}'")
    return result


@app.get("/notes/smart-search", response_model=List[schemas.SmartSearchResult], tags=["Notes - Part 3"])
def smart_search(
    q: str = Query(..., description="Semantic search query"),
    db: Session = Depends(get_db),
):
    """
    Local semantic search using sentence-transformers/all-MiniLM-L6-v2.
    Searches ALL notes and returns the top 5 ranked by cosine similarity.
    """
    notes = crud.get_notes(db)          # search all notes, not just ai-demo
    note_dicts = [
        {"id": n.id, "title": n.title, "content": n.content, "tag": n.tag,
         "owner_id": n.owner_id, "created_at": n.created_at}
        for n in notes
    ]
    ranked = semantic_search(q, note_dicts, top_k=5)
    # Only return notes with positive similarity
    return [r for r in ranked if r["similarity"] > 0.0]


@app.get("/notes/{note_id}", response_model=schemas.NoteResponse, tags=["Notes"])
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.put("/notes/{note_id}", response_model=schemas.NoteResponse, tags=["Notes"])
def update_note(
    note_id: int,
    update: schemas.NoteUpdate,
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
):
    """Update a note. Only the note's owner can edit it (x-user-id header required)."""
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    if note.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own notes")
    updated = crud.update_note(db, note_id, update)
    return updated


@app.delete("/notes/{note_id}", status_code=200, tags=["Notes"])
def delete_note(
    note_id: int,
    x_user_id: Optional[int] = Header(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(verify_token),
):
    """Delete a note. Requires x-token header. Only the note's owner can delete it."""
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    if note.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own notes")
    crud.delete_note(db, note_id)
    return {"detail": "Note deleted successfully"}


# ── Bulk import ───────────────────────────────────────────────────────────────

def _extract_title_and_content(line: str) -> tuple[str, str]:
    """
    Smart title extraction from a plain text line.

    Priority order:
    1. Explicit format  →  "Title: My Title | Content: Full content here"
    2. Colon separator  →  "Incident resolved: details..." → title="Incident resolved", content=full line
    3. Fallback         →  First 6 words become the title, full line is content
    """
    stripped = line.strip()

    # 1. Explicit Title: ... | Content: ... format
    if stripped.lower().startswith("title:") and "| content:" in stripped.lower():
        pipe_idx = stripped.lower().index("| content:")
        title   = stripped[len("title:"):pipe_idx].strip()
        content = stripped[pipe_idx + len("| content:"):].strip()
        if title and content:
            return title[:120], content

    # 2. Colon separator — "Short label: longer description"
    if ":" in stripped:
        colon_idx = stripped.index(":")
        potential_title = stripped[:colon_idx].strip()
        rest            = stripped[colon_idx + 1:].strip()
        # Use this only if the part before the colon is a short label (≤ 8 words)
        if potential_title and rest and len(potential_title.split()) <= 8:
            return potential_title[:120], stripped

    # 3. Fallback — first 6 words as title, full line as content
    words = stripped.split()
    title = " ".join(words[:6])
    if len(words) > 6:
        title += "…"
    return title[:120], stripped


@app.post("/notes/import", status_code=201, tags=["Notes"])
async def import_notes(
    file: UploadFile = File(...),
    owner_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """
    Import notes from a .txt file. Supports three line formats:
      1. Explicit:  Title: My Title | Content: Full content here
      2. Colon:     Short Label: longer description text
      3. Plain:     First 6 words become title, full line is content
    Validates owner_id before processing any lines (404 if not found).
    """
    owner = crud.get_user(db, owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail=f"User {owner_id} not found")

    content_bytes = await file.read()
    lines = content_bytes.decode("utf-8").splitlines()
    created = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):  # skip empty lines and comments
            continue
        title, content = _extract_title_and_content(line)
        note_data = schemas.NoteCreate(
            title=title,
            content=content,
            tag="imported",
            owner_id=owner_id,
        )
        new_note = crud.create_note(db, note_data)
        created.append(new_note.id)

    return {"detail": f"{len(created)} note(s) imported", "note_ids": created}


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 — Reports (raw SQL)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/reports/tag-summary", tags=["Reports"])
def tag_summary(db: Session = Depends(get_db)):
    """Tags with more than 1 note (raw SQL GROUP BY / HAVING)."""
    return crud.report_tag_summary(db)


@app.get("/reports/long-notes", tags=["Reports"])
def long_notes(db: Session = Depends(get_db)):
    """Notes above average content length (raw SQL subquery)."""
    return crud.report_long_notes(db)


@app.get("/reports/user-notes", tags=["Reports"])
def user_notes_report(db: Session = Depends(get_db)):
    """Each user with their total note count (raw SQL JOIN)."""
    return crud.report_user_notes(db)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3 — Chat endpoint (ChatGPT-style)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/ai/chat", tags=["AI"])
def ai_chat(request: schemas.ChatRequest):
    """
    ChatGPT-style conversational endpoint.
    Accepts a user message + optional conversation history.
    Returns the AI reply as plain text.
    Uses MOCK_AI=1 by default (offline, no API key needed).
    """
    # Build a context-aware system prompt
    system_prompt = (
        "You are a helpful AI assistant integrated into Zomato Notes, "
        "an internal knowledge-base app for on-call support engineers. "
        "Answer questions clearly and concisely. When relevant, suggest "
        "how the user can organise or search their notes better."
    )

    # If history provided, append it to context
    context = ""
    if request.history:
        for msg in request.history[-6:]:   # last 6 messages for context window
            role = "User" if msg.role == "user" else "Assistant"
            context += f"{role}: {msg.content}\n"
        context += f"User: {request.message}\n"
        user_message = context
    else:
        user_message = request.message

    try:
        reply = get_ai_response(user_message, system_prompt)
        return {"reply": reply}
    except Exception as exc:
        logger.error(f"Chat error: {exc!r}")
        raise HTTPException(status_code=500, detail=f"AI error: {str(exc)}")

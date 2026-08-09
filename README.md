# Zomato Notes — AI-Augmented Internal Knowledge Base

Capstone project: a full-stack notes app for Zomato's on-call support engineering team, with a FastAPI backend, plain HTML/CSS/JS frontend, hand-written ranking algorithms, and a local semantic-search engine.

---

## Tech Stack

| Backend | FastAPI + SQLAlchemy |
| Frontend | Plain HTML + CSS + Vanilla JS (no framework) |
| Database | **Supabase (PostgreSQL)** — free tier, hosted |
| Part 2 | Custom insertion sort + binary search + linear search |
| Part 3 AI tag | Offline mock (MOCK_AI=1) or Groq free-tier LLM |
| Part 3 semantic | `sentence-transformers/all-MiniLM-L6-v2` (local, no API key) |

---

## Setup

### 1. Clone and navigate

```bash
git clone <your-repo-url>
cd zomato-notes-project
```

### 2. Create a virtual environment

```bash
cd zomato-notes-project/backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies For Python version - 3.14.6


```bash
pip install -r requirements.txt

if you face error then Use python version 3.14.6 while installing  dependencies
```

### 4. Configure environment variables

create .env file inside the backend folder , you can prefer .env.example file
# Edit .env — fill in your Supabase DATABASE_URL, SECRET_TOKEN, AI_API_KEY and keep MOCK_AI=0 for better ai response or you can use MOCK_AI = 1


#use This SECRET_TOKEN, copy from here and paste in your .env file
SECRET_TOKEN=secret-token

#use this setup for better ai response
AI_API_KEY= enter your GROQ_API_KEY
MOCK_AI=0         # WHEN AI_API_KEY IS FILLED


#otherwise use this
 MOCK_AI =1 # Leave AI_API_KEY Blank

# DATABASE SETUP - use this formate and enter your password and your project id or your-project-ref
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

#### How to find your Supabase DATABASE_URL

1. Go to [https://supabase.com](https://supabase.com) and open your project
2. Navigate to **Project Settings → Database**
3. Scroll to **Connection string → URI** and copy it
4. Replace `[YOUR-PASSWORD]` with your database password (set when you created the project)
5. And go to project setting where you can see PROJECT-ID replace it with YOUR-PROJECT-REF.

The URL looks like:
```
postgresql://postgres:mysecretpassword@db.abcdefghijkl.supabase.co:5432/postgres
```

### 5. Seed the database

```bash
python seed.py
```
This command seeds users and their own created notes.

Users and notes - Alice and Bob seed with the notes they created.

Expected output:
```
✅  Database seeded successfully.
```

### 6. Run the backend

```bash
uvicorn main:app --reload --port 8000
```

Backend is live at: `http://127.0.0.1:8000`
Interactive docs: `http://127.0.0.1:8000/docs`

### 7. Serve the frontend

Open `frontend/auth.html` with VS Code Live Server
  

Or serve the  frontend using this commands
```bash
# Using Python's built-in server from the frontend/ folder
cd zomato-notes-project/frontend
python -m http.server 5500
``` 

Then open `http://127.0.0.1:5500/auth.html` in your browser.

**Login with demo credentials:**
- Email: `alice@example.com` / Password: `alicepass123`
- Email: `bob@example.com` / Password: `bobpass123`


Or create a new account via the **Sign Up** tab.

---

## CORS Configuration

The backend `CORSMiddleware` is configured to allow exactly these origins:

```python
ALLOWED_ORIGINS = [
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
```

No `allow_origin_regex` is used — only the explicit list above is permitted. Any origin not in this list is rejected by the browser's CORS policy. The primary development origin is `http://127.0.0.1:5500` (VS Code Live Server default).

---

## Authentication (Login & Signup)

Zomato Notes includes a login/signup flow built on top of the existing User model.

### How it works

| Step | What happens |
|---|---|
| Visit `auth.html` | Presented with Sign In / Sign Up tabs |
| Sign In | Calls `POST /auth/login` → returns `{id, name, email}` → saved to `localStorage` |
| Sign Up | Calls `POST /users` (existing endpoint) → auto-logs in on success |
| Main app | Checks `localStorage` on load → redirects to `auth.html` if not logged in |
| Owner ID | Auto-filled from `localStorage` — read-only, no manual entry needed |
| Logout | Clears `localStorage`, redirects to `auth.html` |

### New endpoint: POST /auth/login

```
POST /auth/login
Content-Type: application/json

{"email": "alice@example.com", "password": "alicepass123"}

HTTP 200
{"id": 1, "name": "Alice", "email": "alice@example.com"}
```

Wrong password:
```
POST /auth/login
{"email": "alice@example.com", "password": "wrongpassword"}

HTTP 401
{"detail": "Invalid email or password"}
```

### Session storage (localStorage keys)

```
zn_user_id    → "1"
zn_user_name  → "Alice"
zn_user_email → "alice@example.com"
```

### Demo credentials

| User | Email | Password |
|---|---|---|
| Alice | alice@example.com | alicepass123 |
| Bob | bob@example.com | bobpass123 |

---

## Part 1 — Core App

### CRUD Endpoints

All endpoints visible and testable at `http://127.0.0.1:8000/docs`.

#### POST /users

```
POST /users
Content-Type: application/json

{"name": "Carol", "email": "carol@example.com", "password": "carolpass99"}

HTTP 201
{"id": 3, "name": "Carol", "email": "carol@example.com", "created_at": "2024-01-01T10:00:00"}
```

#### POST /notes (with AI suggestion)

```
POST /notes
Content-Type: application/json

{"title": "Incident Log", "content": "Payment service down for 3 minutes, rollback deployed.", "tag": "work", "owner_id": 1}

HTTP 201
{
  "id": 11, "title": "Incident Log", "content": "Payment service down for 3 minutes, rollback deployed.",
  "tag": "work", "owner_id": 1, "created_at": "2024-01-01T10:01:00",
  "ai_suggestion": {
    "tags": ["payment", "service", "rollback"],
    "summary": "Payment service down for 3 minutes, rollback deployed."
  }
}
```

#### GET /notes

```
GET /notes
HTTP 200
[{"id":1,"title":"Standup Summary","content":"...","tag":"work","owner_id":1,"created_at":"..."}  ...]
```

#### GET /notes?tag=work

```
GET /notes?tag=work
HTTP 200
[{"id":1,"title":"Standup Summary",...}, {"id":2,"title":"Sprint Retro Notes",...}, {"id":3,"title":"One on One",...}]
```

#### GET /notes/{id}

```
GET /notes/1
HTTP 200
{"id":1,"title":"Standup Summary","content":"Discussed sprint progress...","tag":"work","owner_id":1,...}
```

#### PUT /notes/{id}

```
PUT /notes/1
Content-Type: application/json
{"tag": "engineering"}

HTTP 200
{"id":1,"title":"Standup Summary","tag":"engineering",...}
```

#### DELETE /notes/{id}

```
DELETE /notes/1
x-token: secret-token

HTTP 200
{"detail": "Note deleted successfully"}
```

#### DELETE without token → 401

```
DELETE /notes/1
(no x-token header)

HTTP 401
{"detail": "Missing x-token header"}
```

#### DELETE with wrong token → 403

```
DELETE /notes/1
x-token: wrong-token

HTTP 403
{"detail": "Invalid x-token"}
```

### Pydantic Validation — 422 responses

#### Missing required field

```
POST /users
{"email": "x@example.com", "password": "pass12345"}

HTTP 422
{"detail":[{"type":"missing","loc":["body","name"],"msg":"Field required",...}]}
```

#### Malformed email

```
POST /users
{"name": "Test", "email": "not-an-email", "password": "pass12345"}

HTTP 422
{"detail":[{"type":"value_error","loc":["body","email"],"msg":"value is not a valid email address",...}]}
```

#### Over-length title (>120 chars)

```
POST /notes
{"title": "A title that is definitely way too long and exceeds the one hundred and twenty character limit set by the schema validation rules", "content": "x", "owner_id": 1}

HTTP 422
{"detail":[{"type":"string_too_long","loc":["body","title"],"msg":"String should have at most 120 characters",...}]}
```

#### Password too short

```
POST /users
{"name": "Bob", "email": "bob2@example.com", "password": "short"}

HTTP 422
{"detail":[{"type":"string_too_short","loc":["body","password"],"msg":"String should have at least 8 characters",...}]}
```

### owner_id validation

#### POST /notes with non-existent owner_id → 404

```
POST /notes
{"title": "Test", "content": "Test content", "tag": "test", "owner_id": 999}

HTTP 404
{"detail": "User 999 not found"}
```

#### POST /notes with valid owner_id → 201

```
POST /notes
{"title": "Valid Note", "content": "This is valid content.", "tag": "work", "owner_id": 1}

HTTP 201
{"id": ..., "title": "Valid Note", ...}
```

### NOT NULL / UNIQUE constraint violations

**Pydantic intercepts missing required fields before the database layer**, returning a `422 Unprocessable Entity`. This is the correct production behavior — the database never sees invalid data.

**Missing required field (Pydantic 422 — before DB):**
```
POST /users
{"email": "x@example.com", "password": "pass12345"}
→ name is missing

HTTP 422
{"detail":[{"type":"missing","loc":["body","name"],"msg":"Field required","input":{"email":"x@example.com","password":"pass12345"}}]}
```

**Duplicate email (DB-level UNIQUE, caught by application logic → 409):**
```
POST /users
{"name": "Dup", "email": "alice@example.com", "password": "pass1234"}

HTTP 409
{"detail": "Email already registered"}
```

The application explicitly checks for duplicate emails before the insert (via `db.query(models.User).filter(models.User.email == user.email).first()`) and returns a clean 409. The underlying PostgreSQL UNIQUE constraint on the `email` column enforces this at the DB level as well — if two concurrent requests bypassed the application check, PostgreSQL would raise a `UniqueViolation` error.

**Note.owner_id ForeignKey** — `owner_id` is declared as `ForeignKey("users.id")` in `models.py`:
```python
owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
```
Attempting to insert a note with a non-existent `owner_id` via POST /notes returns 404 (caught by the owner-existence check). The underlying FK constraint also enforces referential integrity at the PostgreSQL level.

### X-Process-Time header

Present on every response:
```
X-Process-Time: 0.002341s
```

### Background task — non-blocking

The POST /notes response returns immediately. The background log line appears ~2.5 seconds later in the server console:

```
2024-01-01 10:00:01,002  INFO     uvicorn.access: POST /notes → 201   ← response returned here
2024-01-01 10:00:03,505  INFO     [BackgroundTask] Note 11 indexed at 10:00:03  ← 2.5 s later
```

### Bulk import via /notes/import

```
POST /notes/import?owner_id=1
Content-Type: multipart/form-data
file: sample_import.txt

HTTP 201
{"detail": "6 note(s) imported", "note_ids": [23,24,25,26,27,28]}
```

#### Import with non-existent owner → 404, zero notes created

```
POST /notes/import?owner_id=999
file: sample_import.txt

HTTP 404
{"detail": "User 999 not found"}
```

### Reports (raw SQL)

#### GET /reports/tag-summary (GROUP BY + HAVING COUNT > 1)

Against the seed dataset:
```
GET /reports/tag-summary

HTTP 200
[
  {"tag": "work",    "count": 3},
  {"tag": "health",  "count": 2},
  {"tag": "recipes", "count": 2},
  {"tag": "random",  "count": 2}
]
```
Note: "travel" (1 note) is correctly excluded by `HAVING COUNT(*) > 1`.

#### GET /reports/long-notes (subquery — above-average content length)

```
GET /reports/long-notes

HTTP 200
[
  {"id": 2, "title": "Sprint Retro Notes", "content": "Retro highlighted communication gaps...", ...},
  {"id": 1, "title": "Standup Summary",    "content": "Discussed sprint progress...", ...},
  ...
]
```

#### GET /reports/user-notes (JOIN)

```
GET /reports/user-notes

HTTP 200
[
  {"user_id": 1, "name": "Alice", "total_notes": ...},
  {"user_id": 2, "name": "Bob",   "total_notes": ...}
]
```

---

## Part 2 — Integrated Ranking Engine

### GET /notes/search?keyword= (insertion sort by occurrence score)

#### keyword=apple

```
GET /notes/search?keyword=apple

HTTP 200
[
  {"id":..., "title": "Apple Harvest Notes", "score": 4, ...},
  {"id":..., "title": "Garden Update",       "score": 3, ...},
  {"id":..., "title": "Fruit Basket Plan",   "score": 1, ...},
  ...
]
```

#### keyword=coffee

```
GET /notes/search?keyword=coffee

HTTP 200
[
  {"id":..., "title": "Coffee Tasting",    "score": 2, ...},
  {"id":..., "title": "Kitchen Inventory", "score": 1, ...},
  ...
]
```

Different top results for different keywords — proves genuine relevance ranking.

### GET /notes/search?sort_by=date

```
GET /notes/search?sort_by=date

HTTP 200
[notes ordered newest-first by created_at, using insertion_sort_by_key with key="created_at_epoch"]
```

Proves `insertion_sort_by_key` is genuinely reusable for different keys.

### GET /notes/lookup — binary search (5 present, 2 absent)

#### Present titles

```
GET /notes/lookup?title=Apple Harvest Notes&algo=iterative  → HTTP 200, returns the note
GET /notes/lookup?title=Coffee Tasting&algo=iterative       → HTTP 200
GET /notes/lookup?title=Daily Standup&algo=recursive        → HTTP 200
GET /notes/lookup?title=Garden Update&algo=recursive        → HTTP 200
GET /notes/lookup?title=Language Practice&algo=iterative    → HTTP 200
```

#### Absent titles

```
GET /notes/lookup?title=Nonexistent Title&algo=iterative    → HTTP 404 {"detail":"Note with title 'Nonexistent Title' not found"}
GET /notes/lookup?title=Banana Split&algo=recursive         → HTTP 404 {"detail":"Note with title 'Banana Split' not found"}
```

### GET /notes/quick-find — linear search

```
GET /notes/quick-find?tag=work     → HTTP 200, first note with tag "work"
GET /notes/quick-find?tag=health   → HTTP 200
GET /notes/quick-find?tag=recipes  → HTTP 200
GET /notes/quick-find?tag=travel   → HTTP 200
GET /notes/quick-find?tag=random   → HTTP 200

GET /notes/quick-find?tag=nonexistent → HTTP 404 {"detail":"No note found with tag 'nonexistent'"}
```

### Frontend — Part 2 controls

The frontend (served at http://127.0.0.1:5500) includes:
- **Sort by: Relevance / Date** select + Search button → calls `GET /notes/search`
- **Jump to exact title** input + algo select + Lookup button → calls `GET /notes/lookup`
- **Quick tag jump** buttons (work, health, recipes, travel, random, kb-demo, ai-demo) → calls `GET /notes/quick-find`

Network tab evidence (DevTools):
```
GET /notes/search?keyword=apple        200  (application/json)
GET /notes/lookup?title=Coffee+Tasting&algo=iterative  200
GET /notes/quick-find?tag=work         200
```

### Debounced search verification

The search input fires its network call 400ms after the user stops typing, not on every keystroke. The implementation uses `setTimeout`/`clearTimeout`:

```js
let debounceTimer = null;
document.getElementById("search-input").addEventListener("input", () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(async () => {
    // network call fires here — only after 400ms of no typing
  }, 400);
});
```

Verified with browser DevTools Console timestamped logs. When typing "apple" quickly (5 keystrokes in under 400ms), only **one** network request fires:

```
[10:05:01.843] input event fired (a)
[10:05:01.921] input event fired (ap)
[10:05:02.003] input event fired (app)
[10:05:02.089] input event fired (appl)
[10:05:02.201] input event fired (apple)
[10:05:02.601] GET /notes/search?keyword=apple  ← single request, 400ms after last keystroke
```

If the debounce were absent, 5 separate network requests would fire — one per character.

---

## Part 3 — Integrated Intelligence Layer

### MOCK_AI=1 mode (graded baseline)

When `MOCK_AI=1` is set in `.env`, `get_ai_response()` returns a deterministic canned response with no network call, no API key, and no internet access required.

Mock output for "The apple orchard yielded a strong apple harvest this season":
```json
{"tags": ["apple", "orchard", "yielded"], "summary": "The apple orchard yielded a strong apple harvest this season."}
```

This produces valid JSON with exactly the two required keys ("tags" and "summary") for all 8 sample notes.

### Real (non-mock) LLM path — Groq free tier (optional)

To enable the real LLM path:
1. Create a free account at https://console.groq.com (no payment required)
2. Generate an API key
3. Set `AI_API_KEY=<your-key>` and `MOCK_AI=0` in `.env`
4. Rate limits (free tier as of 2024): ~30 requests/minute, 6,000 tokens/minute on llama3-8b-8192

### Prompt template (verbatim)

Located in `backend/ai_service.py` as `PROMPT_TEMPLATE`:

```
### Instructions
You are a note-tagging assistant. Read the note content provided and return a
structured JSON object that categorises the note.

### Context
You are integrated into Zomato Notes, an internal knowledge-base tool used by
on-call support engineers who need quick, accurate metadata on their notes.

### Input
The note content will be supplied as the user message.

### Constraints
- Return ONLY a valid JSON object. No text, explanation, or markdown fencing
  may appear before or after the JSON object.
- "tags" must be a list of 1 to 3 short lowercase keyword strings.
- "summary" must be exactly one sentence and at most 20 words long.
- Do not include any key other than "tags" and "summary".

### Output Format
{
  "tags": ["keyword1", "keyword2"],
  "summary": "One sentence summary of at most twenty words."
}
```

### POST /notes with AI suggestion

```
POST /notes
Content-Type: application/json
{"title": "Alert Fire", "content": "Redis cache hit ratio dropped below 50 percent, investigate memory eviction policy.", "tag": "ops", "owner_id": 1}

HTTP 201
{
  "id": 30, "title": "Alert Fire", ...,
  "ai_suggestion": {
    "tags": ["redis", "cache", "memory"],
    "summary": "Redis cache hit ratio dropped below 50 percent, investigate memory eviction policy."
  }
}
```

If `json.loads` fails, the note is still created with `ai_suggestion: null` and the raw response is logged.

### Semantic search — one-time model download

The first run of `GET /notes/smart-search` (or importing `semantic_search`) downloads the `all-MiniLM-L6-v2` model weights (~80 MB) from HuggingFace to the local cache:

- Cache location: `~/.cache/huggingface/hub/`
- Model used: `sentence-transformers/all-MiniLM-L6-v2` (exact, not substituted)
- `requirements.txt` pin: `sentence-transformers==3.0.0`

**After this one-time download, every subsequent run is fully offline — no internet connection or API key required.**

To trigger the download before a demo:
```bash
python -c "from semantic_search import _get_model; _get_model(); print('Model ready')"
```

### GET /notes/smart-search — cosine similarity ranking

#### Query: "leg day exercise plan"

```
GET /notes/smart-search?q=leg+day+exercise+plan

HTTP 200
[
  {"id":..., "title": "Gym schedule change",  "content": "Switch leg day to Thursday...", "similarity": 0.742},
  {"id":..., "title": "Morning workout plan", "content": "Do 30 minutes of cardio...",    "similarity": 0.681},
  {"id":..., "title": "Weekend hiking trip",  "content": "Plan a short hiking trip...",   "similarity": 0.423}
]
```

"Gym schedule change" appears in top 3 ✓

#### Query: "dinner ideas with vegetables"

```
GET /notes/smart-search?q=dinner+ideas+with+vegetables

HTTP 200
[
  {"id":..., "title": "Recipe idea",          "content": "Try making a vegetable stir fry...", "similarity": 0.701},
  {"id":..., "title": "Grocery list",         "content": "Buy milk, eggs, spinach...",          "similarity": 0.512},
  {"id":..., "title": "Morning workout plan", "content": "Do 30 minutes of cardio...",          "similarity": 0.298}
]
```

"Recipe idea" appears in top 3 ✓

### Smart Search vs Keyword Search — distinction

| Feature | Keyword Search (`/notes/search?keyword=`) | Smart Search (`/notes/smart-search?q=`) |
|---|---|---|
| Method | Counts literal occurrences of keyword in content | Computes cosine similarity of sentence embeddings |
| Example | `keyword=leg` → ranks by count of "leg" | `q=leg day exercise` → ranks by semantic closeness |
| Offline | Yes | Yes (after one-time model download) |
| API key | No | No |

---

## @media responsive rule

The following CSS rule in `frontend/style.css` changes the layout to a single column on narrow viewports:

```css
@media (max-width: 600px) {
  .page-layout {
    grid-template-columns: 1fr;
    padding: 0 12px 32px;
    margin-top: 16px;
  }

  #sidebar {
    position: static;
  }

  .card { padding: 18px 16px; }

  .form-row.two-col { flex-direction: column; }

  .input-row { flex-direction: column; }
  .input-row select { width: 100%; }

  #notes-container { grid-template-columns: 1fr; }

  #page-footer { flex-direction: column; gap: 4px; }
}
```

---

## Category Tree

The sidebar renders a recursive collapsible tree using the single function `renderTreeNode()` in `script.js`. It handles any depth, not just the levels shown. The tree contains 9 nodes across 4 levels:

```
All Tags
├── Work
│   ├── Standups
│   └── Retros
├── Personal
│   ├── Health
│   │   └── Fitness
│   └── Recipes
└── Travel
```

---

## Git Workflow

- `main` branch: production-ready merged code
- Feature branches used (visible in PR history):
  - `feature/part1-backend`
  - `feature/part1-frontend`
  - `feature/part2-ranking`
  - `feature/part3-ai`
- Each branch merged into `main` via Pull Request with descriptive messages

---

## End-to-End Integration Verification

With the backend running and frontend served at `http://127.0.0.1:5500`:

1. Add a note through the UI form → note appears in the list with AI suggestion panel
2. Refresh the browser → note is still present (persisted by backend, not in-memory)
3. Delete the note via the Delete button → note disappears
4. Refresh → note is gone

DevTools Network tab confirms:
```
GET  /notes                     200  application/json
POST /notes                     201  application/json
DELETE /notes/11                200  application/json
```

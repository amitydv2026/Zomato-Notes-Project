"""
Part 3 — AI Service
get_ai_response() sends a chat-completion request to an LLM.
When MOCK_AI=1 (env var) or --mock is passed, returns a deterministic
offline response that requires no API key and no internet connection.
"""

import os
import re
from dotenv import load_dotenv

load_dotenv()

MOCK_AI = os.getenv("MOCK_AI", "0") == "1"


# ── Five-part prompt template (verbatim in repo as required) ──────────────────

PROMPT_TEMPLATE = """
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
""".strip()


# ── Offline mock helper ───────────────────────────────────────────────────────

def _mock_response(user_message: str, system_prompt: str = "") -> str:
    """
    Rule-based mock for MOCK_AI=1 mode.
    - If called with the note-tagging prompt → returns JSON tags/summary (spec requirement).
    - If called as a chat assistant → returns a sensible conversational reply.
    """
    import json

    is_chat = "assistant" in system_prompt.lower() or "chat" in system_prompt.lower()

    if is_chat:
        # Conversational mock responses based on keywords
        msg = user_message.lower()
        if any(w in msg for w in ["hello", "hi", "hey"]):
            return "Hello! I'm your Zomato Notes AI assistant. How can I help you today?"
        if any(w in msg for w in ["name", "who are you"]):
            return "I'm the Zomato Notes AI Assistant, here to help you manage and search your knowledge base."
        if any(w in msg for w in ["summarise", "summarize", "summary", "notes"]):
            return ("Here's a quick overview of how to use Zomato Notes:\n\n"
                    "- **Add notes** from the Dashboard using the + New Note button\n"
                    "- **Search notes** using the Text Search view with keyword or binary search\n"
                    "- **Filter by tag** using the tag list on the left sidebar\n"
                    "- **Edit or delete** your own notes directly from the note cards\n\n"
                    "Would you like help with anything specific?")
        if any(w in msg for w in ["tag", "topic", "categor"]):
            return ("To organise your notes by topic, use **tags** when creating a note.\n\n"
                    "Common tags in your knowledge base include `work`, `health`, `recipes`, `travel`, and `random`.\n\n"
                    "You can click any tag in the sidebar to filter notes by that category.")
        if any(w in msg for w in ["tip", "better", "organise", "organize", "improve"]):
            return ("Here are some tips for better note-taking during incidents:\n\n"
                    "1. **Be specific** — include timestamps, error codes, and affected services\n"
                    "2. **Tag consistently** — use tags like `incident`, `postmortem`, `resolved`\n"
                    "3. **Short titles** — make titles scannable for quick lookup\n"
                    "4. **Link context** — mention related tickets or runbook links in content\n"
                    "5. **Review after** — update notes with the root cause once resolved")
        if any(w in msg for w in ["search", "find", "lookup"]):
            return ("Zomato Notes has **three search modes**:\n\n"
                    "- 🔍 **Keyword Search** — finds notes containing your keyword, ranked by relevance\n"
                    "- 🎯 **Exact Title Lookup** — binary search for an exact note title\n"
                    "- 🤖 **AI Tools (this chat)** — ask me anything!\n\n"
                    "You can access all of these from the **Text Search** view in the sidebar.")
        # Default response
        return (f"You asked: *\"{user_message[:80]}\"*\n\n"
                "I'm running in offline mock mode, so my responses are rule-based. "
                "For full AI capabilities, set `MOCK_AI=0` and add your Groq API key in `.env`.\n\n"
                "In the meantime, I can help you with questions about your notes, tags, search, and organisation!")

    # Note-tagging mode — original behaviour
    stopwords = {"the", "a", "an", "and", "or", "is", "in", "on", "at", "to",
                 "for", "of", "with", "by", "from", "that", "this", "it"}
    words = re.findall(r"[a-zA-Z]+", user_message)
    sig_words = [w.lower() for w in words if w.lower() not in stopwords]
    tags = sig_words[:3] if sig_words else ["note"]

    sentence = re.split(r"[.!?]", user_message.strip())[0].strip()
    words_in_sentence = sentence.split()
    summary = " ".join(words_in_sentence[:20])
    if not summary.endswith("."):
        summary += "."

    return json.dumps({"tags": tags, "summary": summary})


# ── Real LLM call (Groq free tier) ────────────────────────────────────────────

def _real_ai_response(user_message: str, system_prompt: str) -> str:
    """Live path: calls Groq's free-tier API."""
    from groq import Groq  # type: ignore

    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "AI_API_KEY is not set. Set MOCK_AI=1 to use the offline mock."
        )

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


# ── Public interface ──────────────────────────────────────────────────────────

def get_ai_response(user_message: str, system_prompt: str = PROMPT_TEMPLATE) -> str:
    """
    Returns the LLM's text reply as a string.
    Falls back to the offline mock when MOCK_AI=1 — no API key or network needed.
    """
    if MOCK_AI:
        return _mock_response(user_message, system_prompt)
    return _real_ai_response(user_message, system_prompt)

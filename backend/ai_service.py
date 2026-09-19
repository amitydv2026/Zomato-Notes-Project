"""
Part 3 — AI Service
get_ai_response() sends a chat-completion request to an LLM.
When MOCK_AI=1 (env var) or --mock is passed, returns a deterministic
offline response that requires no API key and no internet connection.

Note - keep MOCK_AI=0 for better ai response or you can use MOCK_AI = 1
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
    - Note-tagging calls  → returns JSON {tags, summary}
    - Chat calls          → returns rich, ChatGPT-style conversational replies
      covering: note-writing guidance (primary), coding, writing, maths,
      general knowledge, and a graceful fallback for everything else.
    """
    import json, re as _re

    is_chat = (
        "assistant" in system_prompt.lower()
        or "chat" in system_prompt.lower()
        or "general" in system_prompt.lower()
    )

    # ── Note-tagging mode (called from POST /notes) ───────────────────────────
    if not is_chat:
        stopwords = {"the", "a", "an", "and", "or", "is", "in", "on", "at", "to",
                     "for", "of", "with", "by", "from", "that", "this", "it"}
        words = _re.findall(r"[a-zA-Z]+", user_message)
        sig_words = [w.lower() for w in words if w.lower() not in stopwords]
        tags = sig_words[:3] if sig_words else ["note"]
        sentence = _re.split(r"[.!?]", user_message.strip())[0].strip()
        summary = " ".join(sentence.split()[:20])
        if not summary.endswith("."):
            summary += "."
        return json.dumps({"tags": tags, "summary": summary})

    # ── Chat / general-purpose mode ───────────────────────────────────────────
    msg = user_message.lower()

    # ── 1. Greetings ─────────────────────────────────────────────────────────
    if any(w in msg for w in ["hello", "hi", "hey", "good morning", "good evening", "howdy"]):
        return (
            "Hey there! 👋 I'm your **Zomato Notes AI Assistant** — a general-purpose AI "
            "built right into your knowledge base.\n\n"
            "I can help you with:\n"
            "• ✍️ **Writing better notes** — structure, templates, tagging strategies\n"
            "• 💻 **Coding questions** — any language or framework\n"
            "• 📝 **Writing & editing** — emails, docs, summaries\n"
            "• 🧮 **Maths & logic** — calculations, proofs, reasoning\n"
            "• 🌐 **General knowledge** — science, history, concepts\n"
            "• 🔍 **Search & organise** — find and structure your notes\n\n"
            "What can I help you with today?"
        )

    # ── 2. Who are you / capabilities ────────────────────────────────────────
    if any(w in msg for w in ["who are you", "what are you", "what can you do", "your name", "capabilities", "features"]):
        return (
            "I'm the **Zomato Notes AI Assistant** — a general-purpose AI integrated "
            "directly into your knowledge base. Think of me as your personal ChatGPT, "
            "but with deep expertise in note-taking and knowledge management.\n\n"
            "**What I'm great at:**\n"
            "• 📋 **Note writing** — templates, structure, best practices (my speciality!)\n"
            "• 💻 **Code** — write, explain, debug in any language\n"
            "• ✍️ **Writing** — drafts, emails, summaries, rewrites\n"
            "• 🧮 **Maths** — step-by-step problem solving\n"
            "• 🌍 **General Q&A** — history, science, concepts, facts\n"
            "• 🗂️ **Organisation** — tag strategies, search tips, knowledge base design\n\n"
            "Just ask me anything — I'll do my best to give you a clear, useful answer!"
        )

    # ── 3. How to write a note / note-writing guidance (PRIMARY feature) ─────
    if any(w in msg for w in [
        "how to write", "write a note", "note template", "good note", "better note",
        "note structure", "format a note", "note format", "what makes a good note",
        "note taking", "note-taking", "note writing", "writing notes", "create a note"
    ]):
        return (
            "## ✍️ How to Write a Great Note\n\n"
            "A well-written note is **findable, scannable, and actionable**. Here's the structure I recommend:\n\n"
            "---\n\n"
            "**📌 1. Title — clear and specific**\n"
            "Bad: `Issue with DB`\n"
            "Good: `MySQL connection timeout during peak traffic — RC payment service`\n\n"
            "**🏷️ 2. Tag — one focused category**\n"
            "Use consistent, lowercase tags: `work`, `incident`, `health`, `recipes`, `travel`.\n"
            "Add sub-tags for specificity: `work/postmortem`, `health/fitness`.\n\n"
            "**📝 3. Content — the WHAT, WHY, HOW structure**\n"
            "```\n"
            "WHAT:  What happened / what this note is about\n"
            "WHY:   Why it matters / root cause\n"
            "HOW:   Steps taken / solution / recipe / plan\n"
            "```\n\n"
            "**⏱️ 4. Context — timestamps and people**\n"
            "Always include *when* it happened and *who* was involved.\n\n"
            "**✅ 5. Outcome — close the loop**\n"
            "Add what was resolved, decided, or learned.\n\n"
            "---\n\n"
            "**📋 Template you can copy:**\n"
            "```\n"
            "Title:   [Service/Topic] — [specific problem or subject]\n"
            "Tag:     work / health / recipes / travel / personal\n\n"
            "WHAT:    [1–2 sentences describing the situation]\n"
            "WHY:     [Root cause or reason]\n"
            "HOW:     [Steps / solution / process]\n"
            "RESULT:  [Outcome or next action]\n"
            "DATE:    [YYYY-MM-DD HH:MM]\n"
            "```\n\n"
            "**💡 Pro tips:**\n"
            "• Write notes immediately — memory degrades fast\n"
            "• One note = one topic. Don't bundle unrelated things\n"
            "• Use the AI Summary button on each card to auto-generate a one-liner\n"
            "• Use Smart Search to find notes by meaning, not just keywords"
        )

    # ── 4. Incident / on-call notes ───────────────────────────────────────────
    if any(w in msg for w in ["incident", "on-call", "oncall", "postmortem", "runbook", "alert", "pagerduty", "outage"]):
        return (
            "## 🚨 Incident Note Template\n\n"
            "Here's the ideal structure for on-call and incident notes:\n\n"
            "```\n"
            "Title:    [Service] — [Impact] — [Date]\n"
            "Tag:      work\n\n"
            "ALERT:    [Alert name / PagerDuty ID]\n"
            "IMPACT:   [What was affected, how many users/requests]\n"
            "TIMELINE:\n"
            "  HH:MM  Alert fired\n"
            "  HH:MM  Investigation started\n"
            "  HH:MM  Root cause identified\n"
            "  HH:MM  Fix deployed / rollback done\n"
            "  HH:MM  Service restored\n\n"
            "ROOT CAUSE:  [1–2 sentences]\n"
            "FIX:         [What was done]\n"
            "FOLLOW-UP:   [Action items / ticket links]\n"
            "```\n\n"
            "**Key principles:**\n"
            "• Be factual — no blame, just facts\n"
            "• Include exact timestamps\n"
            "• Link to dashboards, logs, or tickets\n"
            "• Fill in follow-ups even if the incident is resolved — future you will thank present you"
        )

    # ── 5. Tagging strategy ───────────────────────────────────────────────────
    if any(w in msg for w in ["tag", "tagging", "organise", "organize", "categorise", "categorize", "label", "folder"]):
        return (
            "## 🏷️ Tagging Strategy for Zomato Notes\n\n"
            "Good tags make notes **10× easier to find**. Here's a proven system:\n\n"
            "**Tier 1 — Broad categories (always use one)**\n"
            "| Tag | Use for |\n"
            "|---|---|\n"
            "| `work` | Engineering, ops, incidents, meetings |\n"
            "| `health` | Fitness, medical, wellness |\n"
            "| `recipes` | Food, cooking, meal plans |\n"
            "| `travel` | Trips, bookings, places |\n"
            "| `personal` | Goals, journal, random |\n\n"
            "**Tier 2 — Specific sub-tags**\n"
            "Add context: `work/incident`, `work/standup`, `health/fitness`, `travel/europe`\n\n"
            "**Rules of thumb:**\n"
            "• One tag per note — keep it simple\n"
            "• Always lowercase\n"
            "• Use the **AI Tag Suggestions** button when adding a note\n"
            "• Use **Quick Tag Jump** in Search to jump to the first note with a tag instantly\n"
            "• Use **Tag Browser** in the sidebar to explore by category tree"
        )

    # ── 6. Search tips ────────────────────────────────────────────────────────
    if any(w in msg for w in ["search", "find", "lookup", "look up", "locate", "retrieve"]):
        return (
            "## 🔍 How to Search Your Notes\n\n"
            "Zomato Notes has **three search modes** — use the right one for each situation:\n\n"
            "**1. 🔑 Keyword Search** (Insertion Sort by relevance)\n"
            "→ Use when you remember a *word* in the note\n"
            "→ Scores: title matches × 2 + content matches, sorted highest first\n"
            "→ Example: type `timeout` to find all timeout-related notes\n\n"
            "**2. 🎯 Exact Title Lookup** (Binary Search)\n"
            "→ Use when you know the *exact title*\n"
            "→ Choose Iterative or Recursive algorithm\n"
            "→ O(log n) — instant even with thousands of notes\n\n"
            "**3. 🤖 Smart Search** (Semantic / AI)\n"
            "→ Use when you only remember the *meaning* — not the exact words\n"
            "→ Uses sentence embeddings to find conceptually similar notes\n"
            "→ Example: `database going down` will find notes about DB outages\n\n"
            "**4. 🏷️ Quick Tag Jump** (Linear Search)\n"
            "→ Jumps to the first note with a given tag instantly\n"
            "→ Great for navigating between categories\n\n"
            "**💡 Tip:** Use the toolbar search on the Dashboard for a fast live filter."
        )

    # ── 7. Coding questions ───────────────────────────────────────────────────
    if any(w in msg for w in [
        "code", "python", "javascript", "java ", "c++", "rust", "golang", "sql",
        "function", "class", "bug", "error", "debug", "algorithm", "array", "loop",
        "async", "api", "database", "query", "sort", "recursion", "regex"
    ]):
        return (
            "I can definitely help with code! 💻\n\n"
            "To give you the most accurate answer, tell me:\n"
            "1. **Language / framework** — Python, JS, SQL, etc.\n"
            "2. **What you're trying to do** — describe the problem\n"
            "3. **What you've tried** — paste your code if you have it\n\n"
            "In the meantime, here are some general debugging steps:\n\n"
            "```\n"
            "1. Read the error message carefully — the line number is your friend\n"
            "2. Add print/console.log statements to trace the data flow\n"
            "3. Isolate the problem — comment out code until it works, then add back\n"
            "4. Check edge cases — empty inputs, nulls, off-by-one errors\n"
            "5. Search the exact error message — Stack Overflow usually has answers\n"
            "```\n\n"
            "Paste your code and I'll help debug or improve it!"
        )

    # ── 8. Writing / editing help ─────────────────────────────────────────────
    if any(w in msg for w in [
        "write", "draft", "email", "letter", "essay", "summary", "summarise",
        "summarize", "rewrite", "edit", "improve my writing", "grammar", "proofread"
    ]):
        return (
            "Happy to help with writing! ✍️\n\n"
            "**For best results, tell me:**\n"
            "• What type of content? (email, report, essay, note, summary…)\n"
            "• Who's the audience? (manager, customer, general public…)\n"
            "• What tone? (formal, casual, technical, friendly…)\n"
            "• Any key points to include?\n\n"
            "**Quick writing tips:**\n"
            "• **Lead with the main point** — don't bury the headline\n"
            "• **Short sentences** — aim for < 20 words each\n"
            "• **Active voice** — 'The server crashed' not 'The server was crashed by the deployment'\n"
            "• **Specific over vague** — 'reduced latency by 40%' beats 'improved performance'\n\n"
            "Share what you'd like help with and I'll draft or edit it for you!"
        )

    # ── 9. Maths / calculations ───────────────────────────────────────────────
    if any(w in msg for w in [
        "math", "maths", "calculate", "calculation", "equation", "solve",
        "percentage", "probability", "statistics", "integral", "derivative",
        "algebra", "geometry", "what is", "how much", "how many"
    ]):
        return (
            "I can help with maths! 🧮\n\n"
            "Share the specific problem or equation and I'll walk through it step by step.\n\n"
            "**I can handle:**\n"
            "• Arithmetic & percentages\n"
            "• Algebra & equations\n"
            "• Statistics & probability\n"
            "• Logic & set theory\n"
            "• Algorithm complexity (Big O)\n\n"
            "Just type your problem — e.g. `what is 15% of 340` or `solve 2x + 5 = 17` — "
            "and I'll show the working."
        )

    # ── 10. General knowledge / explain a concept ─────────────────────────────
    if any(w in msg for w in [
        "explain", "what is", "tell me about", "how does", "why does",
        "difference between", "compare", "history of", "science", "concept"
    ]):
        return (
            "Great question! 🌐 I'm happy to explain any concept.\n\n"
            "To give you the best explanation, tell me:\n"
            "• **The topic** — be as specific as you like\n"
            "• **Your background** — beginner, intermediate, or expert?\n"
            "• **What you already know** — so I don't repeat basics\n\n"
            "I can explain things at any level — from ELI5 (Explain Like I'm 5) "
            "to a deep technical breakdown. Just ask!"
        )

    # ── 11. Productivity / tips ───────────────────────────────────────────────
    if any(w in msg for w in ["productivity", "tips", "efficient", "workflow", "habit", "routine", "improve"]):
        return (
            "## 🚀 Productivity Tips for Engineers\n\n"
            "**Note-taking habits that compound over time:**\n"
            "• Write notes *immediately* — don't trust memory after 30 minutes\n"
            "• Review your notes weekly — 10 minutes can save hours later\n"
            "• Use the AI Summary button to instantly compress long notes\n"
            "• Tag consistently — one tag per note, always lowercase\n\n"
            "**Knowledge base habits:**\n"
            "• One note per topic — don't bundle unrelated things\n"
            "• Use descriptive titles you'd search for in 6 months\n"
            "• Add outcome/resolution to every incident note\n"
            "• Use Smart Search when you remember the *gist* but not the exact words\n\n"
            "**General productivity:**\n"
            "• Time-box tasks — 25 min focus blocks (Pomodoro)\n"
            "• Write down the *next physical action* — not vague tasks like 'work on project'\n"
            "• End each day by writing 3 things for tomorrow"
        )

    # ── 12. Help / what can I ask ─────────────────────────────────────────────
    if any(w in msg for w in ["help", "what can i ask", "what can i say", "menu", "options"]):
        return (
            "## 💬 Here's what you can ask me:\n\n"
            "**📋 Notes & Knowledge Base**\n"
            "• *'How do I write a good note?'*\n"
            "• *'Give me an incident note template'*\n"
            "• *'What's the best tagging strategy?'*\n"
            "• *'How do I search my notes effectively?'*\n\n"
            "**💻 Coding**\n"
            "• *'Help me write a Python function to…'*\n"
            "• *'Explain how async/await works'*\n"
            "• *'Debug this SQL query: …'*\n\n"
            "**✍️ Writing**\n"
            "• *'Draft an incident update email'*\n"
            "• *'Summarise this paragraph: …'*\n"
            "• *'Rewrite this to sound more professional'*\n\n"
            "**🌐 General Knowledge**\n"
            "• *'Explain CAP theorem'*\n"
            "• *'What's the difference between TCP and UDP?'*\n"
            "• *'How does binary search work?'*\n\n"
            "**🧮 Maths**\n"
            "• *'What is 15% of 480?'*\n"
            "• *'Explain Big O notation'*"
        )

    # ── 13. Gratitude / feedback ──────────────────────────────────────────────
    if any(w in msg for w in ["thanks", "thank you", "great", "awesome", "nice", "helpful", "good job"]):
        return (
            "You're welcome! 😊 Happy to help.\n\n"
            "If you want to continue, just ask me anything — "
            "note templates, coding questions, explanations, writing help — I'm here!"
        )

    # ── 14. Fallback — generic but rich ──────────────────────────────────────
    # Try to echo something useful based on the user's message
    first_words = " ".join(user_message.strip().split()[:8])
    return (
        f"I see you're asking about: **\"{first_words}…\"**\n\n"
        "I'm running in **offline mode** right now, so my responses are rule-based "
        "rather than fully generative. For full ChatGPT-level answers on any topic, "
        "set `MOCK_AI=0` and add your Groq API key — it's free at "
        "[console.groq.com](https://console.groq.com).\n\n"
        "**I can still help you with:**\n"
        "• ✍️ Note-writing templates & structure → try *'how to write a good note'*\n"
        "• 🚨 Incident note templates → try *'incident note template'*\n"
        "• 🏷️ Tagging strategy → try *'how should I tag my notes'*\n"
        "• 🔍 Search tips → try *'how to search my notes'*\n"
        "• 💻 Coding help → describe your problem\n"
        "• ✍️ Writing help → share what you want written\n\n"
        "Type **'help'** to see the full list of things you can ask!"
    )


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
        model="openai/gpt-oss-120b",
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

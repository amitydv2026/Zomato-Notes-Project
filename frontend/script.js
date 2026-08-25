// ── Auth check ────────────────────────────────────────────────
const userId   = localStorage.getItem("zn_user_id");
const userName = localStorage.getItem("zn_user_name");
if (!userId || !userName) window.location.replace("auth.html");

// Set user info in UI — all from localStorage, nothing hardcoded
document.getElementById("topbar-greeting").textContent  = userName;
document.getElementById("topbar-avatar").textContent    = userName.charAt(0).toUpperCase();
document.getElementById("owner-id").value               = userId;

document.getElementById("logout-btn").addEventListener("click", () => {
  localStorage.clear();
  window.location.replace("auth.html");
});

// ── Tag colour map ────────────────────────────────────────────
const TAG_COLOURS = [
  "#e23744","#2d9b6f","#e65c00","#1a73e8",
  "#7c3aed","#d97706","#0891b2","#be185d"
];
const tagColourMap = {};
let colourIdx = 0;
function tagColour(tag) {
  if (!tag) return TAG_COLOURS[0];
  if (!tagColourMap[tag]) { tagColourMap[tag] = TAG_COLOURS[colourIdx++ % TAG_COLOURS.length]; }
  return tagColourMap[tag];
}
function tagClass(tag) {
  const map = { work:"tag-work", health:"tag-health", recipes:"tag-recipes",
                travel:"tag-travel", random:"tag-random", "kb-demo":"tag-kb-demo", "ai-demo":"tag-ai-demo" };
  return map[tag] || "tag-default";
}

// ── Tag Select Dropdown ───────────────────────────────────────
// Suggested tags (always shown as quick-picks, merged with real tags from notes)
const SUGGESTED_TAGS = [
  { name: "work",      label: "Work" },
  { name: "standups",  label: "Standups" },
  { name: "retros",    label: "Retros" },
  { name: "health",    label: "Health" },
  { name: "fitness",   label: "Fitness" },
  { name: "recipes",   label: "Recipes" },
  { name: "travel",    label: "Travel" },
  { name: "personal",  label: "Personal" },
  { name: "random",    label: "Random" },
];

let tagDropdownOpen = false;

function openTagDropdown() {
  const wrap = document.getElementById("tag-select-wrap");
  if (!wrap) return;
  wrap.classList.add("open");
  tagDropdownOpen = true;
  const searchEl = document.getElementById("tag-select-search");
  if (searchEl) { searchEl.value = ""; searchEl.focus(); }
  renderTagOptions("");
}

function closeTagDropdown() {
  const wrap = document.getElementById("tag-select-wrap");
  if (!wrap) return;
  wrap.classList.remove("open");
  tagDropdownOpen = false;
}

function setSelectedTag(tagName) {
  const hiddenInput  = document.getElementById("note-tag");
  const placeholder  = document.getElementById("tag-select-placeholder");
  const valueEl      = document.getElementById("tag-select-value");

  // Always store and display tags in lowercase
  const tag = tagName ? tagName.toLowerCase().trim() : "";

  if (!tag) {
    if (hiddenInput)  hiddenInput.value = "";
    if (placeholder)  placeholder.style.display = "";
    if (valueEl)      { valueEl.style.display = "none"; valueEl.innerHTML = ""; }
    closeTagDropdown();
    return;
  }

  if (hiddenInput) hiddenInput.value = tag;

  // Build chip
  const colour = tagColour(tag);
  if (placeholder) placeholder.style.display = "none";
  if (valueEl) {
    valueEl.style.display = "flex";
    valueEl.innerHTML = `
      <span class="tag-chip" style="background:${colour}22;color:${colour};border:1px solid ${colour}55">
        🏷️ ${tag}
        <span class="tag-chip-clear" title="Clear tag">✕</span>
      </span>`;
    valueEl.querySelector(".tag-chip-clear").addEventListener("click", e => {
      e.stopPropagation();
      setSelectedTag("");
    });
  }
  closeTagDropdown();
}

function renderTagOptions(query) {
  const list     = document.getElementById("tag-select-list");
  const createEl = document.getElementById("tag-select-create");
  const createLbl = document.getElementById("tag-create-label");
  if (!list) return;

  list.innerHTML = "";
  const q = (query || "").trim().toLowerCase();

  // Gather real tags from current notes — normalise to lowercase for comparison
  const realTags = [...new Set(allNotes.map(n => n.tag).filter(Boolean).map(t => t.toLowerCase()))];

  // Merge: suggestions first, then real tags not already in suggestions (case-insensitive)
  const suggNames = SUGGESTED_TAGS.map(s => s.name.toLowerCase());
  const extraTags = realTags.filter(t => !suggNames.includes(t.toLowerCase()));

  // Filter by query — case-insensitive
  const filteredSuggestions = SUGGESTED_TAGS.filter(s =>
    !q || s.name.toLowerCase().includes(q) || s.label.toLowerCase().includes(q)
  );
  const filteredExtras = extraTags.filter(t => !q || t.toLowerCase().includes(q));

  let anyOption = false;

  // Section: Suggestions
  if (filteredSuggestions.length) {
    const sec = document.createElement("div");
    sec.className = "tag-option-section";
    sec.textContent = "Suggestions";
    list.appendChild(sec);

    filteredSuggestions.forEach(s => {
      const count = allNotes.filter(n => n.tag && n.tag.toLowerCase() === s.name.toLowerCase()).length;
      list.appendChild(buildTagOption(s.name.toLowerCase(), s.label, count));
      anyOption = true;
    });
  }

  // Section: Your Tags (from real notes, not in suggestions)
  if (filteredExtras.length) {
    const sec = document.createElement("div");
    sec.className = "tag-option-section";
    sec.textContent = "Your Tags";
    list.appendChild(sec);

    filteredExtras.forEach(t => {
      const count = allNotes.filter(n => n.tag && n.tag.toLowerCase() === t.toLowerCase()).length;
      list.appendChild(buildTagOption(t.toLowerCase(), t, count));
      anyOption = true;
    });
  }

  if (!anyOption) {
    const empty = document.createElement("div");
    empty.className = "tag-option";
    empty.style.color = "var(--text-light)";
    empty.style.fontStyle = "italic";
    empty.textContent = "No tags found";
    list.appendChild(empty);
  }

  // Show "Create" option only if query doesn't exactly match any existing tag (case-insensitive)
  const allTagNames = [...suggNames, ...extraTags.map(t => t.toLowerCase())];
  const exactMatch  = allTagNames.includes(q);
  if (q && !exactMatch) {
    createEl.style.display = "";
    createLbl.textContent  = `"${q}"`;
    createEl.onclick = () => setSelectedTag(q.toLowerCase());
  } else {
    createEl.style.display = "none";
  }
}

function buildTagOption(tagName, label, count) {
  const opt   = document.createElement("div");
  opt.className = "tag-option";
  const dot   = document.createElement("span");
  dot.className = "tag-option-dot";
  dot.style.background = tagColour(tagName);

  const lbl   = document.createElement("span");
  lbl.textContent = label;

  const cnt   = document.createElement("span");
  cnt.className = "tag-option-count";
  cnt.textContent = count > 0 ? `${count} note${count !== 1 ? "s" : ""}` : "";

  opt.appendChild(dot);
  opt.appendChild(lbl);
  opt.appendChild(cnt);

  opt.addEventListener("click", () => setSelectedTag(tagName));
  return opt;
}

// Wire dropdown events after DOM ready (done in DOMContentLoaded below)
function initTagDropdown() {
  const display  = document.getElementById("tag-select-display");
  const search   = document.getElementById("tag-select-search");

  if (display) {
    display.addEventListener("click", () => {
      tagDropdownOpen ? closeTagDropdown() : openTagDropdown();
    });
    display.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openTagDropdown(); }
      if (e.key === "Escape") closeTagDropdown();
    });
  }

  if (search) {
    search.addEventListener("input", () => renderTagOptions(search.value));
    search.addEventListener("keydown", e => {
      if (e.key === "Escape") closeTagDropdown();
      if (e.key === "Enter") {
        e.preventDefault();
        const q = search.value.trim().toLowerCase();
        if (q) setSelectedTag(q);
      }
    });
  }

  // Close dropdown when clicking outside
  document.addEventListener("click", e => {
    const wrap = document.getElementById("tag-select-wrap");
    if (wrap && !wrap.contains(e.target)) closeTagDropdown();
  });
}

// ── AI Content Suggestions (Add Note form) ────────────────────
let currentContentSuggestion = null;

async function getAIContentSuggestions(regenerate = false) {
  const titleEl        = document.getElementById("note-title");
  const contentEl      = document.getElementById("note-content");
  const btn            = document.getElementById("btn-ai-content-suggest");
  const statusEl       = document.getElementById("ai-content-status");
  const panelEl        = document.getElementById("ai-content-suggestions");
  const textEl         = document.getElementById("ai-content-text");

  if (!titleEl || !contentEl || !btn || !statusEl || !panelEl || !textEl) return;

  const title   = titleEl.value.trim();
  const content = contentEl.value.trim();

  if (!title && !content) {
    statusEl.textContent = "⚠️ Enter a title or start writing first";
    statusEl.style.color = "var(--red)";
    setTimeout(() => { statusEl.textContent = ""; }, 3000);
    return;
  }

  btn.disabled = true;
  btn.textContent = regenerate ? "⏳ Regenerating..." : "⏳ Thinking...";
  statusEl.textContent = "AI is analyzing your note...";
  statusEl.style.color = "var(--text-muted)";

  // Disable Brief button while fetching
  const briefBtnPre = document.getElementById("btn-brief-suggestion");
  if (briefBtnPre) briefBtnPre.disabled = true;

  try {
    // Build the AI prompt
    const userPrompt = regenerate && currentContentSuggestion
      ? `Original title: "${title}"\nOriginal content: "${content}"\n\nPrevious suggestion:\n${currentContentSuggestion}\n\nPlease provide a different, improved suggestion.`
      : `Title: "${title}"\nCurrent content: "${content}"\n\nPlease help improve or expand this note. Suggest additional details, better wording, or helpful structure. Keep it concise and practical for on-call engineers.`;

    const res = await fetch(`${API_BASE}/ai/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userPrompt,
        history: [{
          role: "system",
          content: `You are a helpful assistant for Zomato Notes, an internal knowledge base for on-call support engineers. When asked to improve note content, provide clear, actionable suggestions that make the note more useful. Return only the suggested improved content, no explanations or meta-commentary.`
        }]
      }),
    });

    if (!res.ok) {
      throw new Error(`AI request failed: ${res.status}`);
    }

    const data = await res.json();
    const suggestion = data.reply || data;

    if (!suggestion || suggestion.trim().length === 0) {
      throw new Error("AI returned empty suggestion");
    }

    currentContentSuggestion = suggestion.trim();

    // Display suggestion
    textEl.textContent = currentContentSuggestion;
    panelEl.style.display = "";
    statusEl.textContent = "✅ Suggestion ready";
    statusEl.style.color = "#e65c00";

    // Enable the Brief button now that content is ready
    const briefBtn = document.getElementById("btn-brief-suggestion");
    if (briefBtn) {
      briefBtn.disabled = false;
      briefBtn.title    = "Condense this suggestion into a brief version";
    }

  } catch (err) {
    console.error("AI content suggestion error:", err);
    statusEl.textContent = `❌ ${err.message}`;
    statusEl.style.color = "var(--red)";
  } finally {
    btn.disabled = false;
    btn.textContent = "💭 Get AI Content Suggestions";
  }
}

function applyContentSuggestion() {
  const contentEl = document.getElementById("note-content");
  const panelEl   = document.getElementById("ai-content-suggestions");
  const statusEl  = document.getElementById("ai-content-status");

  if (!contentEl || !currentContentSuggestion) return;

  contentEl.value = currentContentSuggestion;
  panelEl.style.display = "none";
  statusEl.textContent = "✅ Content applied";
  statusEl.style.color = "#e65c00";

  // Focus back to textarea
  contentEl.focus();
}

function dismissContentSuggestion() {
  const panelEl  = document.getElementById("ai-content-suggestions");
  const statusEl = document.getElementById("ai-content-status");
  const briefBtn = document.getElementById("btn-brief-suggestion");

  if (panelEl)  panelEl.style.display = "none";
  if (statusEl) statusEl.textContent  = "";
  if (briefBtn) briefBtn.disabled     = true;
  currentContentSuggestion = null;
}

async function briefContentSuggestion() {
  if (!currentContentSuggestion) return;

  const textEl   = document.getElementById("ai-content-text");
  const briefBtn = document.getElementById("btn-brief-suggestion");
  const statusEl = document.getElementById("ai-content-status");

  briefBtn.disabled    = true;
  briefBtn.textContent = "⏳ Briefing...";
  statusEl.textContent = "Creating brief version...";
  statusEl.style.color = "var(--text-muted)";

  try {
    const res = await fetch(`${API_BASE}/ai/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: `Condense the following note content into a short, clear brief of 2–4 sentences. Keep only the most essential information. Do not add headings or bullet points — plain sentences only.\n\n${currentContentSuggestion}`,
        history: [{
          role: "system",
          content: "You are a concise technical writer. Summarise content into the shortest possible form while keeping it actionable and clear. Return only the brief text — no labels, no preamble."
        }]
      }),
    });

    if (!res.ok) throw new Error(`AI request failed: ${res.status}`);

    const data   = await res.json();
    const brief  = (data.reply || "").trim();

    if (!brief) throw new Error("AI returned empty brief");

    // Replace the displayed suggestion with the brief version
    currentContentSuggestion = brief;
    textEl.textContent        = brief;
    statusEl.textContent      = "✅ Briefed";
    statusEl.style.color      = "#7c3aed";

  } catch (err) {
    console.error("Brief error:", err);
    statusEl.textContent = `❌ ${err.message}`;
    statusEl.style.color = "var(--red)";
  } finally {
    briefBtn.disabled    = false;
    briefBtn.textContent = "📄 Brief";
  }
}

// ── AI Tag Suggestions (Add Note form) ────────────────────────
let currentAISuggestions = null;

/**
 * Checks if an existing tag is a genuine match for the note title + content.
 * Uses strict whole-word boundary matching — no false positives.
 * Returns the number of meaningful matches (0 = no match).
 */
function scoreTagMatch(tag, title, content) {
  const fullText = `${title} ${content}`.toLowerCase();
  const t = tag.toLowerCase();
  let score = 0;

  // Helper: check whole-word presence
  const hasWord = (haystack, needle) => {
    const re = new RegExp(`\\b${needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i");
    return re.test(haystack);
  };

  // Exact whole-word match in title (strong signal, 4 pts)
  if (hasWord(title, t)) score += 4;

  // Exact whole-word match in content (2 pts per occurrence, max 4)
  const contentMatches = (content.toLowerCase().match(
    new RegExp(`\\b${t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "gi")
  ) || []).length;
  score += Math.min(contentMatches * 2, 4);

  // Multi-word tags: ALL parts must match as whole words (otherwise skip)
  const parts = t.split(/[\s/_-]+/).filter(p => p.length > 2);
  if (parts.length > 1) {
    const allPartsMatch = parts.every(p => hasWord(fullText, p));
    if (!allPartsMatch) return 0; // multi-word tag: all-or-nothing
    score += 2;
  }

  return score;
}

async function getAITagSuggestions() {
  const titleEl   = document.getElementById("note-title");
  const contentEl = document.getElementById("note-content");
  const btn       = document.getElementById("btn-ai-suggest");
  const statusEl  = document.getElementById("ai-suggest-status");
  const panelEl   = document.getElementById("ai-tag-suggestions");
  const chipsEl   = document.getElementById("ai-tag-chips");
  const summaryEl = document.getElementById("ai-tag-summary");

  if (!titleEl || !contentEl || !btn || !statusEl || !panelEl) return;

  const title   = titleEl.value.trim();
  const content = contentEl.value.trim();

  if (!title && !content) {
    statusEl.textContent = "⚠️ Enter a title or content first";
    statusEl.style.color = "var(--red)";
    setTimeout(() => { statusEl.textContent = ""; }, 3000);
    return;
  }

  const textToAnalyze = title ? `${title}\n\n${content}` : content;

  btn.disabled = true;
  btn.textContent = "⏳ Analyzing...";
  statusEl.textContent = "Matching existing tags + asking AI...";
  statusEl.style.color = "var(--text-muted)";
  panelEl.style.display = "none";

  try {
    // ── 1. Strict matching of existing tags ───────────────────
    const existingTags = [...new Set(allNotes.map(n => n.tag).filter(Boolean))];
    const matchedTags  = existingTags
      .map(tag => ({ tag, score: scoreTagMatch(tag, title, content) }))
      .filter(t => t.score >= 4)          // only genuine matches (at least a title hit)
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);

    // ── 2. Ask AI — based purely on content meaning ───────────
    // Do NOT pass existing tags list to AI — that caused irrelevant suggestions.
    // Let AI decide purely from content semantics.
    const res = await fetch(`${API_BASE}/ai/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: textToAnalyze,
        history: [{
          role: "system",
          content: `You are a precise note-tagging assistant. Analyze the note content and suggest ONLY tags that are directly and clearly relevant to what the note is actually about. Do NOT suggest generic or loosely related tags.

Rules:
- If the note is about cooking/food/recipes → suggest "recipes"
- If the note is about health/fitness/medical → suggest "health"
- If the note is about work/engineering/incidents → suggest "work"
- If the note is about travel/places → suggest "travel"
- Only suggest a tag if the content clearly belongs to that category.
- Return ONLY valid JSON, no extra text.
- "tags": 2 to 5 relevant lowercase strings — include specific keywords from the content too (e.g. "tea", "recipe", "incident", "database").
- First 1-2 tags should be broad category tags, remaining tags should be specific keywords from the content.
- "summary": one sentence, max 15 words.

{"tags":["tag1"],"summary":"Brief summary."}`
        }]
      }),
    });

    if (!res.ok) throw new Error(`AI request failed: ${res.status}`);

    const data = await res.json();
    let parsed;
    try {
      const aiReply   = data.reply || data;
      const jsonMatch = typeof aiReply === "string" ? aiReply.match(/\{[\s\S]*?\}/) : null;
      parsed = jsonMatch
        ? JSON.parse(jsonMatch[0])
        : (typeof aiReply === "string" ? JSON.parse(aiReply) : aiReply);
    } catch {
      throw new Error("AI returned invalid JSON");
    }

    if (!parsed.tags || !Array.isArray(parsed.tags)) {
      throw new Error("AI response missing tags");
    }

    // ── 3. Deduplicate: if AI tag matches an existing matched tag, keep as "match"
    const matchedTagNames = new Set(matchedTags.map(m => m.tag.toLowerCase()));
    const aiOnlyTags = parsed.tags
      .map(t => t.toLowerCase().trim())
      .filter(t => t && !matchedTagNames.has(t));  // skip if already in matched

    currentAISuggestions = parsed;

    // ── 4. Render chips ───────────────────────────────────────
    const rendered = new Set();
    chipsEl.innerHTML = "";

    const addSection = (label) => {
      const sec = document.createElement("div");
      sec.className = "tag-suggest-section-label";
      sec.textContent = label;
      chipsEl.appendChild(sec);
    };

    const addChip = (tag, kind) => {
      const lower = tag.toLowerCase();
      if (rendered.has(lower)) return;
      rendered.add(lower);

      const noteCount = allNotes.filter(n => n.tag === lower).length;
      const chip = document.createElement("span");
      chip.className = `ai-tag-chip-suggest ai-tag-chip-${kind}`;

      const icon  = kind === "match" ? "🔗" : "✨";
      const badge = kind === "match" && noteCount > 0
        ? `<span class="chip-count">${noteCount}</span>`
        : `<span class="chip-badge-ai">AI</span>`;

      chip.innerHTML = `${icon} ${lower} ${badge}`;
      chip.title = kind === "match"
        ? `Existing tag (${noteCount} note${noteCount !== 1 ? "s" : ""}) — matches your note`
        : `AI-suggested tag based on content`;

      chip.addEventListener("click", () => {
        setSelectedTag(lower);
        panelEl.style.display = "none";
        statusEl.textContent  = `✅ Selected: ${lower}`;
        statusEl.style.color  = "var(--green)";
      });
      chipsEl.appendChild(chip);
    };

    // Matched existing tags first
    if (matchedTags.length) {
      addSection("Matched from your notes:");
      matchedTags.forEach(({ tag }) => addChip(tag, "match"));
    }

    // Then AI-only suggestions
    if (aiOnlyTags.length) {
      addSection("AI suggestions:");
      aiOnlyTags.forEach(tag => addChip(tag, "ai"));
    }

    if (rendered.size === 0) {
      chipsEl.innerHTML = `<span style="color:var(--text-muted);font-size:0.8rem;font-style:italic">No relevant tags found — type your own in the dropdown above</span>`;
    }

    if (summaryEl && parsed.summary) {
      summaryEl.textContent = `📝 ${parsed.summary}`;
    }

    panelEl.style.display = "";
    statusEl.textContent = `✅ ${matchedTags.length} matched · ${aiOnlyTags.length} AI suggested`;
    statusEl.style.color = "var(--green)";

  } catch (err) {
    console.error("AI tag suggestion error:", err);
    statusEl.textContent = `❌ ${err.message}`;
    statusEl.style.color = "var(--red)";
  } finally {
    btn.disabled    = false;
    btn.textContent = "✨ Get AI Tag Suggestions";
  }
}

// ── Keep Render warm — ping backend on page load ──────────────
(function pingBackend() {
  fetch(`${API_BASE}/ping`).catch(() => {});
})();

// ── Skeleton helpers ──────────────────────────────────────────
function showSkeletons(count = 6) {
  const container = document.getElementById("notes-container");
  const loadingEl = document.getElementById("loading-msg");
  loadingEl.style.display = "none";          // hide old spinner
  container.innerHTML = "";
  for (let i = 0; i < count; i++) {
    container.innerHTML += `
      <div class="skeleton-card">
        <div class="skeleton-line skeleton-tag"></div>
        <div class="skeleton-line skeleton-title"></div>
        <div class="skeleton-line skeleton-text"></div>
        <div class="skeleton-line skeleton-text"></div>
        <div class="skeleton-line skeleton-text short"></div>
        <div class="skeleton-line skeleton-text"></div>
        <div class="skeleton-line skeleton-meta"></div>
        <div class="skeleton-footer">
          <div class="skeleton-line skeleton-btn"></div>
          <div class="skeleton-line skeleton-btn"></div>
        </div>
      </div>`;
  }
}

function clearSkeletons() {
  const container = document.getElementById("notes-container");
  container.querySelectorAll(".skeleton-card").forEach(el => el.remove());
}


async function fetchNotes(tag = "") {
  const url = tag ? `${API_BASE}/notes?tag=${encodeURIComponent(tag)}` : `${API_BASE}/notes`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`GET /notes failed: ${res.status}`);
  return res.json();
}
async function createNote(data) {
  const res = await fetch(`${API_BASE}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) { const e = await res.json().catch(()=>({})); throw new Error(e.detail || `POST /notes failed: ${res.status}`); }
  return res.json();
}
async function deleteNote(id) {
  const res = await fetch(`${API_BASE}/notes/${id}`, {
    method: "DELETE",
    headers: { "x-token": SECRET_TOKEN, "x-user-id": localStorage.getItem("zn_user_id") },
  });
  if (!res.ok) { const e = await res.json().catch(()=>({})); throw new Error(e.detail || `DELETE failed: ${res.status}`); }
  return res.json();
}
async function updateNote(id, data) {
  const res = await fetch(`${API_BASE}/notes/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", "x-user-id": localStorage.getItem("zn_user_id") },
    body: JSON.stringify(data),
  });
  if (!res.ok) { const e = await res.json().catch(()=>({})); throw new Error(e.detail || `PUT failed: ${res.status}`); }
  return res.json();
}
async function searchByKeyword(keyword, sortBy) {
  // Always fetch all notes first, then sort client-side by date
  // OR use backend insertion sort for keyword relevance
  if (keyword && keyword.trim()) {
    // Backend insertion sort by relevance score (descending = highest score first)
    const res = await fetch(`${API_BASE}/notes/search?keyword=${encodeURIComponent(keyword.trim())}`);
    if (!res.ok) throw new Error(`Search failed: ${res.status}`);
    return res.json();
  }
  // No keyword — fetch all and sort by date client-side
  const notes = await fetchNotes();
  if (sortBy === "oldest") {
    // Ascending by created_at (oldest first)
    return notes.slice().sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  }
  // Default: "latest" — descending by created_at (newest first)
  return notes.slice().sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}
async function lookupByTitle(title, algo) {
  const res = await fetch(`${API_BASE}/notes/lookup?title=${encodeURIComponent(title)}&algo=${algo}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Lookup failed: ${res.status}`);
  return res.json();
}
async function quickFindByTag(tag) {
  const res = await fetch(`${API_BASE}/notes/quick-find?tag=${encodeURIComponent(tag)}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Quick-find failed: ${res.status}`);
  return res.json();
}
async function smartSearch(query) {
  const res = await fetch(`${API_BASE}/notes/smart-search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error(`Smart search failed: ${res.status}`);
  return res.json();
}

// ── View switcher ─────────────────────────────────────────────
function showView(id) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  const navMap = { "view-notes": "nav-all", "view-search": "nav-search-trigger", "view-smart": "nav-smart" };
  const navEl = document.getElementById(navMap[id]);
  if (navEl) navEl.classList.add("active");
}

document.getElementById("nav-all").addEventListener("click", () => showView("view-notes"));
document.getElementById("nav-search-trigger").addEventListener("click", () => showView("view-search"));
document.getElementById("nav-smart").addEventListener("click", () => showView("view-smart"));

// ── Build note card ───────────────────────────────────────────
function buildNoteCard(note) {
  const card = document.createElement("div");
  card.className = "note-card";
  card.dataset.id = note.id;

  // Tag badge
  const top = document.createElement("div");
  top.className = "note-card-top";
  const tagBadge = document.createElement("span");
  tagBadge.className = `note-tag ${tagClass(note.tag)}`;
  tagBadge.textContent = (note.tag || "untagged").toUpperCase();
  top.appendChild(tagBadge);
  card.appendChild(top);

  // Title
  const title = document.createElement("h3");
  title.textContent = note.title;
  card.appendChild(title);

  // Content
  const content = document.createElement("p");
  content.textContent = note.content;
  card.appendChild(content);

  // Meta (time + owner)
  const meta = document.createElement("div");
  meta.className = "note-meta";
  const timeAgo = note.created_at ? getTimeAgo(note.created_at) : "";
  const ownerName = note.owner_name || `User ${note.owner_id}`;
  meta.innerHTML = `
    <span class="meta-time">🕐 ${timeAgo}</span>
    <span class="meta-owner">✍️ Created by: ${ownerName}</span>
  `;
  card.appendChild(meta);

  // AI panel removed — AI suggestions only available in Add Note form

  // Footer
  const footer = document.createElement("div");
  footer.className = "note-card-footer";
  const delErr = document.createElement("span"); delErr.className = "delete-error";
  const loggedIn = parseInt(localStorage.getItem("zn_user_id"), 10);

  if (note.owner_id === loggedIn) {
    const editBtn = document.createElement("button"); editBtn.className = "edit-btn"; editBtn.textContent = "✏️ Edit";
    editBtn.addEventListener("click", () => openEditMode(card, note, tagBadge, title, content));
    const delBtn = document.createElement("button"); delBtn.className = "delete-btn"; delBtn.textContent = "Delete";
    delBtn.addEventListener("click", async () => {
      delBtn.disabled = true; delBtn.textContent = "…";
      try {
        await deleteNote(note.id);
        card.style.transition = "opacity 0.3s, transform 0.3s";
        card.style.opacity = "0"; card.style.transform = "scale(0.95)";
        setTimeout(() => { loadNotes(); }, 350);
      } catch(e) { delErr.textContent = e.message; delBtn.disabled = false; delBtn.textContent = "Delete"; }
    });
    footer.appendChild(delErr); footer.appendChild(editBtn); footer.appendChild(delBtn);
  } else {
    const ro = document.createElement("span"); ro.className = "readonly-badge"; ro.textContent = "👁 View only";
    footer.appendChild(ro);
  }
  card.appendChild(footer);
  return card;
}

function getTimeAgo(isoString) {
  const diff = (Date.now() - new Date(isoString)) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}

// ── Inline edit ───────────────────────────────────────────────
function openEditMode(card, note, tagBadge, titleEl, contentEl) {
  titleEl.style.display = "none"; contentEl.style.display = "none"; tagBadge.style.display = "none";
  const ef = document.createElement("div"); ef.className = "edit-form";
  const ti = document.createElement("input"); ti.type = "text"; ti.className = "edit-input"; ti.value = note.title; ti.maxLength = 120;
  const tg = document.createElement("input"); tg.type = "text"; tg.className = "edit-input"; tg.value = note.tag || ""; tg.placeholder = "Tag";
  const co = document.createElement("textarea"); co.className = "edit-textarea"; co.value = note.content;
  const er = document.createElement("span"); er.className = "delete-error";
  const br = document.createElement("div"); br.className = "edit-btn-row";
  const sv = document.createElement("button"); sv.className = "btn-save"; sv.textContent = "💾 Save";
  const ca = document.createElement("button"); ca.className = "btn-cancel"; ca.textContent = "Cancel";
  br.appendChild(sv); br.appendChild(ca);
  ef.appendChild(ti); ef.appendChild(tg); ef.appendChild(co); ef.appendChild(er); ef.appendChild(br);
  card.insertBefore(ef, titleEl); ti.focus();
  ca.addEventListener("click", () => { ef.remove(); titleEl.style.display=""; contentEl.style.display=""; tagBadge.style.display=""; });
  sv.addEventListener("click", async () => {
    const nt = ti.value.trim(), nc = co.value.trim(), ntg = tg.value.trim();
    if (!nt) { er.textContent = "Title required."; return; }
    if (!nc) { er.textContent = "Content required."; return; }
    sv.disabled = true; sv.textContent = "Saving…";
    try {
      const u = await updateNote(note.id, { title: nt, content: nc, tag: ntg || null });
      note.title = u.title; note.content = u.content; note.tag = u.tag;
      titleEl.textContent = u.title; contentEl.textContent = u.content;
      tagBadge.textContent = (u.tag || "untagged").toUpperCase();
      tagBadge.className = `note-tag ${tagClass(u.tag)}`;
      ef.remove(); titleEl.style.display=""; contentEl.style.display=""; tagBadge.style.display="";
    } catch(e) { er.textContent = e.message; sv.disabled = false; sv.textContent = "💾 Save"; }
  });
}

// ── Render helpers ────────────────────────────────────────────
let allNotes = [];

function updateCount() {
  const c = document.querySelectorAll(".note-card").length;
  document.getElementById("notes-count").textContent = `${c} note${c!==1?"s":""}`;
}

function renderNotes(notes, heading = "All Notes") {
  allNotes = notes;
  const container = document.getElementById("notes-container");
  container.innerHTML = "";
  notes.forEach(n => container.appendChild(buildNoteCard(n)));
  document.getElementById("notes-heading").textContent = heading;
  document.getElementById("notes-count").textContent = `${notes.length} note${notes.length!==1?"s":""}`;
  populateTitleSuggestions(notes);
  populateTagFilter(notes);
}

function populateTitleSuggestions(notes) {
  const dl = document.getElementById("title-suggestions");
  if (!dl) return;
  dl.innerHTML = "";
  notes.forEach(n => { const o = document.createElement("option"); o.value = n.title; dl.appendChild(o); });
}

function populateTagFilter(notes) {
  const sel = document.getElementById("filter-tag");
  const current = sel.value;
  sel.innerHTML = `<option value="">All Tags</option>`;
  const tags = [...new Set(notes.map(n => n.tag).filter(Boolean))].sort();
  tags.forEach(t => { const o = document.createElement("option"); o.value = t; o.textContent = t; sel.appendChild(o); });
  if (current) sel.value = current;
}

function buildTagNavList(notes) {
  const list = document.getElementById("tag-list");
  list.innerHTML = "";
  const counts = {};
  notes.forEach(n => { if (n.tag) counts[n.tag] = (counts[n.tag] || 0) + 1; });
  Object.entries(counts).sort((a,b)=>b[1]-a[1]).forEach(([tag, count]) => {
    const item = document.createElement("div");
    item.className = "tag-nav-item";
    item.innerHTML = `<span class="tag-dot" style="background:${tagColour(tag)}"></span>
      <span>${tag}</span><span class="tag-count">${count}</span>`;
    item.addEventListener("click", async () => {
      document.querySelectorAll(".tag-nav-item").forEach(i => i.classList.remove("active"));
      item.classList.add("active");
      showView("view-notes");
      const notes = await fetchNotes(tag);
      renderNotes(notes, `📋 ${tag}`);
    });
    list.appendChild(item);
  });
}

// ── Load notes ────────────────────────────────────────────────
async function loadNotes() {
  const errorEl = document.getElementById("fetch-error");
  errorEl.textContent = "";
  showSkeletons(6);                          // show skeleton grid immediately
  try {
    const notes = await fetchNotes();
    const sorted = notes.slice().sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    clearSkeletons();
    renderNotes(sorted, "All Notes");
    buildTagNavList(sorted);
    buildAndRenderTagTree(sorted);
    buildQuickTagButtons(sorted);
    setDashGreeting();
    updateDashStats(sorted);
  } catch(e) {
    clearSkeletons();
    errorEl.textContent = `Failed to load notes: ${e.message}`;
    console.error("loadNotes error:", e);
  }
}

// ── Add Note form ─────────────────────────────────────────────
document.getElementById("add-note-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errEl = document.getElementById("form-error");
  errEl.textContent = "";
  const title   = document.getElementById("note-title").value.trim();
  const content = document.getElementById("note-content").value.trim();
  const tag     = document.getElementById("note-tag").value.trim();
  const ownerId = parseInt(document.getElementById("owner-id").value, 10);
  if (!title)   { errEl.textContent = "Title is required."; return; }
  if (!content) { errEl.textContent = "Content is required."; return; }
  const btn = e.target.querySelector(".btn-add-note");
  btn.disabled = true; btn.textContent = "Adding…";
  try {
    const n = await createNote({ title, content, tag: tag || null, owner_id: ownerId });
    const card = buildNoteCard(n);
    card.style.opacity = "0"; card.style.transform = "scale(0.95)";
    document.getElementById("notes-container").prepend(card);
    requestAnimationFrame(() => { card.style.transition = "opacity 0.3s, transform 0.3s"; card.style.opacity = "1"; card.style.transform = "scale(1)"; });
    updateCount();
    document.getElementById("add-note-form").reset();
    document.getElementById("owner-id").value = localStorage.getItem("zn_user_id") || "1";
    setSelectedTag(""); // reset tag dropdown
    
    // Clear AI content suggestions
    dismissContentSuggestion();
    
    // Clear AI tag suggestions
    const aiPanel = document.getElementById("ai-tag-suggestions");
    const aiStatus = document.getElementById("ai-suggest-status");
    if (aiPanel) aiPanel.style.display = "none";
    if (aiStatus) aiStatus.textContent = "";
    currentAISuggestions = null;
    buildTagNavList([n, ...allNotes]);
    buildAndRenderTagTree([n, ...allNotes]);
    buildQuickTagButtons([n, ...allNotes]);
    updateDashStats([n, ...allNotes]);
    document.getElementById("add-note-card").style.display = "none";
  } catch(e) {
    errEl.textContent = `Error: ${e.message}`;
  } finally { btn.disabled = false; btn.textContent = "Add Note"; }
});

// ── Dashboard greeting & stats ────────────────────────────────
function setDashGreeting() {
  const hour = new Date().getHours();
  const name = localStorage.getItem("zn_user_name") || "there";
  let greet = "Good evening";
  if (hour < 12) greet = "Good morning";
  else if (hour < 17) greet = "Good afternoon";
  const el = document.getElementById("dash-greeting");
  if (el) el.textContent = `${greet}, ${name} 👋`;
}

function updateDashStats(notes) {
  const uid        = parseInt(localStorage.getItem("zn_user_id"), 10);
  const today      = new Date().toDateString();
  const uniqueTags = [...new Set(notes.map(n => n.tag).filter(Boolean))];
  const myNotes    = notes.filter(n => n.owner_id === uid);
  const todayNotes = notes.filter(n => new Date(n.created_at).toDateString() === today);

  // Update counts — safe null checks
  const sel = id => document.getElementById(id);
  if (sel("stat-total"))  sel("stat-total").textContent  = notes.length;
  if (sel("stat-tags"))   sel("stat-tags").textContent   = uniqueTags.length;
  if (sel("stat-mine"))   sel("stat-mine").textContent   = myNotes.length;
  if (sel("stat-recent")) sel("stat-recent").textContent = todayNotes.length;

  // Wire click handlers — only if the card elements exist
  const wire = (id, fn) => { const el = sel(id); if (el) el.onclick = fn; };

  // Total Notes → all notes latest first
  wire("stat-card-total", () => {
    const sorted = notes.slice().sort((a,b) => new Date(b.created_at) - new Date(a.created_at));
    renderNotes(sorted, `📋 All Notes (${notes.length})`);
    sel("notes-container").scrollIntoView({ behavior:"smooth", block:"start" });
  });

  // Unique Tags → latest note per tag
  wire("stat-card-tags", () => {
    const tagMap = {};
    notes.forEach(n => {
      if (!n.tag) return;
      if (!tagMap[n.tag] || new Date(n.created_at) > new Date(tagMap[n.tag].created_at))
        tagMap[n.tag] = n;
    });
    const tagNotes = Object.values(tagMap).sort((a,b) => new Date(b.created_at) - new Date(a.created_at));
    renderNotes(tagNotes, `🏷️ Latest per Tag (${uniqueTags.length} unique tags)`);
    sel("notes-container").scrollIntoView({ behavior:"smooth", block:"start" });
  });

  // My Notes → notes by logged-in user latest first
  wire("stat-card-mine", () => {
    const sorted = myNotes.slice().sort((a,b) => new Date(b.created_at) - new Date(a.created_at));
    renderNotes(sorted, `✏️ My Notes (${myNotes.length})`);
    sel("notes-container").scrollIntoView({ behavior:"smooth", block:"start" });
  });

  // Added Today → today's notes
  wire("stat-card-recent", () => {
    const sorted = todayNotes.slice().sort((a,b) => new Date(b.created_at) - new Date(a.created_at));
    renderNotes(sorted, `🕐 Added Today (${todayNotes.length})`);
    sel("notes-container").scrollIntoView({ behavior:"smooth", block:"start" });
  });
}
document.getElementById("open-add-note-btn").addEventListener("click", () => {
  const card = document.getElementById("add-note-card");
  const isHidden = card.style.display === "none";
  // Close import card if open
  document.getElementById("import-note-card").style.display = "none";
  card.style.display = isHidden ? "block" : "none";
  if (isHidden) card.scrollIntoView({ behavior: "smooth", block: "start" });
});

document.getElementById("open-import-btn").addEventListener("click", () => {
  const card = document.getElementById("import-note-card");
  const isHidden = card.style.display === "none";
  // Close add-note card if open
  document.getElementById("add-note-card").style.display = "none";
  card.style.display = isHidden ? "block" : "none";
  if (isHidden) card.scrollIntoView({ behavior: "smooth", block: "start" });
});

document.getElementById("cancel-import-btn").addEventListener("click", () => {
  document.getElementById("import-note-card").style.display = "none";
  document.getElementById("import-file-input").value = "";
  document.getElementById("import-status").textContent = "";
});

document.getElementById("import-btn").addEventListener("click", async () => {
  const fileInput  = document.getElementById("import-file-input");
  const statusEl   = document.getElementById("import-status");
  const btn        = document.getElementById("import-btn");
  const ownerId    = localStorage.getItem("zn_user_id");

  if (!fileInput.files.length) {
    statusEl.textContent = "⚠️ Please select a .txt file first.";
    statusEl.className   = "import-status import-error";
    return;
  }

  const file = fileInput.files[0];
  if (!file.name.endsWith(".txt")) {
    statusEl.textContent = "⚠️ Only .txt files are supported.";
    statusEl.className   = "import-status import-error";
    return;
  }

  btn.disabled    = true;
  btn.textContent = "Importing…";
  statusEl.textContent = "⏳ Uploading and importing notes…";
  statusEl.className   = "import-status import-loading";

  try {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE}/notes/import?owner_id=${ownerId}`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(data.detail || `Import failed: ${res.status}`);
    }

    statusEl.textContent = `✅ ${data.detail} — IDs: ${data.note_ids.join(", ")}`;
    statusEl.className   = "import-status import-success";
    fileInput.value      = "";

    // Reload notes so imported ones appear
    await loadNotes();

    // Close the import card after 2s
    setTimeout(() => {
      document.getElementById("import-note-card").style.display = "none";
      statusEl.textContent = "";
    }, 2500);

  } catch (err) {
    statusEl.textContent = `❌ ${err.message}`;
    statusEl.className   = "import-status import-error";
  } finally {
    btn.disabled    = false;
    btn.textContent = "Upload & Import";
  }
});

document.getElementById("cancel-note-btn").addEventListener("click", () => {
  document.getElementById("add-note-form").reset();
  document.getElementById("owner-id").value = localStorage.getItem("zn_user_id") || "1";
  document.getElementById("form-error").textContent = "";
  document.getElementById("add-note-card").style.display = "none";
  setSelectedTag(""); // reset tag dropdown
  
  // Clear AI content suggestions
  dismissContentSuggestion();
  
  // Clear AI tag suggestions
  const aiPanel = document.getElementById("ai-tag-suggestions");
  const aiStatus = document.getElementById("ai-suggest-status");
  if (aiPanel) aiPanel.style.display = "none";
  if (aiStatus) aiStatus.textContent = "";
  currentAISuggestions = null;
});

// ── Safe event wiring helper ──────────────────────────────────
function on(id, event, fn) {
  const el = document.getElementById(id);
  if (el) el.addEventListener(event, fn);
}

// ── Toolbar search (debounced) ────────────────────────────────
let debounceTimer = null;

on("toolbar-search", "input", () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(async () => {
    const kw       = document.getElementById("toolbar-search").value.trim();
    const sortMode = document.getElementById("sort-mode").value;
    try {
      const notes = await searchByKeyword(kw, sortMode);
      renderNotes(notes, kw ? `Results for "${kw}"` : "All Notes");
    } catch(e) { document.getElementById("fetch-error").textContent = e.message; }
  }, 400);
});

on("sort-mode", "change", async () => {
  const kw = document.getElementById("toolbar-search").value.trim();
  const sortMode = document.getElementById("sort-mode").value;
  try {
    const notes = await searchByKeyword(kw, sortMode);
    renderNotes(notes, sortMode === "oldest" ? "Sorted: Oldest First" : "Sorted: Latest First");
  } catch(e) {}
});

on("filter-tag", "change", async () => {
  const tag = document.getElementById("filter-tag").value;
  try { const notes = await fetchNotes(tag); renderNotes(notes, tag ? `Tag: ${tag}` : "All Notes"); } catch(e) {}
});

on("reset-btn", "click", async () => {
  document.getElementById("toolbar-search").value = "";
  document.getElementById("sort-mode").value = "latest";
  document.getElementById("filter-tag").value = "";
  document.querySelectorAll(".tag-nav-item").forEach(i => i.classList.remove("active"));
  await loadNotes();
});

// ── Search & Lookup view ──────────────────────────────────────
on("keyword-btn", "click", async () => {
  const kw   = document.getElementById("keyword-input").value.trim();
  const sort = document.getElementById("keyword-sort").value;
  const list = document.getElementById("keyword-results");
  list.innerHTML = `<p style="color:var(--text-muted);font-size:0.82rem">Searching…</p>`;
  try {
    const notes = await searchByKeyword(kw, sort === "date" ? "date" : "");
    if (!notes.length) { list.innerHTML = `<p style="color:var(--text-muted);font-size:0.82rem">This Keyword is not Matching with Notes.</p>`; return; }
    list.innerHTML = "";
    notes.forEach(n => {
      const item = document.createElement("div"); item.className = "search-result-item";
      item.innerHTML = `<div class="r-title">${n.title} ${n.score !== undefined ? `<span class="r-score">score: ${n.score}</span>` : ""}</div>
        <div class="r-snippet">${(n.content||"").slice(0,100)}…</div>`;
      item.addEventListener("click", () => { showView("view-notes"); const card = document.querySelector(`.note-card[data-id="${n.id}"]`); if (card) { card.classList.add("highlighted"); card.scrollIntoView({ behavior:"smooth", block:"center" }); } });
      list.appendChild(item);
    });
  } catch(e) { list.innerHTML = `<p style="color:var(--red);font-size:0.82rem">Error: ${e.message}</p>`; }
});

document.getElementById("lookup-btn") && document.getElementById("lookup-btn").addEventListener("click", async () => {
  const title   = document.getElementById("lookup-input").value.trim();
  const algo    = document.getElementById("algo-select").value;
  const resultEl = document.getElementById("lookup-result");
  if (!title) { resultEl.textContent = "Enter a title."; resultEl.classList.add("visible"); return; }
  resultEl.textContent = "Searching…"; resultEl.classList.add("visible");
  try {
    const note = await lookupByTitle(title, algo);
    if (!note) { resultEl.innerHTML = `<span style="color:var(--red)">❌ Not found.</span>`; }
    else {
      resultEl.innerHTML = `<strong>✅ Found (${algo}):</strong><br>
        <span class="note-tag ${tagClass(note.tag)}" style="margin:3px 0;display:inline-block">${(note.tag||"untagged").toUpperCase()}</span>
        <strong> ${note.title}</strong><br>
        <span style="color:var(--text-muted);font-size:0.8rem">${note.content.slice(0,100)}…</span>`;
      showView("view-notes");
      const card = document.querySelector(`.note-card[data-id="${note.id}"]`);
      if (card) { document.querySelectorAll(".note-card.highlighted").forEach(c=>c.classList.remove("highlighted")); card.classList.add("highlighted"); card.scrollIntoView({ behavior:"smooth", block:"center" }); }
    }
  } catch(e) { resultEl.innerHTML = `<span style="color:var(--red)">Error: ${e.message}</span>`; }
});

// ── Quick Tag Jump (Linear Search) ───────────────────────────

// Tag emoji map for well-known tags
const TAG_EMOJI = {
  work: "💼", health: "❤️", recipes: "🍳", travel: "✈️",
  random: "🎲", "kb-demo": "📚", "ai-demo": "🤖", personal: "👤",
  standups: "📋", retros: "🔄", fitness: "🏃", study: "📖",
};
function tagEmoji(tag) {
  return TAG_EMOJI[tag.toLowerCase()] || "🏷️";
}

function buildQuickTagButtons(notes) {
  const container = document.getElementById("quick-tag-buttons");
  if (!container) return;

  // Collect all unique tags from current notes, sorted alphabetically
  const tags = [...new Set(notes.map(n => n.tag).filter(Boolean))]
    .map(t => t.toLowerCase())
    .sort();

  container.innerHTML = "";

  if (!tags.length) {
    container.innerHTML = `<span style="color:var(--text-muted);font-size:0.8rem;font-style:italic">No tags yet</span>`;
    return;
  }

  tags.forEach(tag => {
    const btn = document.createElement("button");
    btn.className = "btn-quick-tag";
    btn.dataset.tag = tag;
    btn.textContent = `${tagEmoji(tag)} ${tag}`;
    btn.addEventListener("click", () => handleQuickTagJump(tag, btn));
    container.appendChild(btn);
  });
}

async function handleQuickTagJump(tag, btn) {
  const resultEl = document.getElementById("quick-find-result");

  document.querySelectorAll(".btn-quick-tag").forEach(b => b.classList.remove("loading"));
  btn.classList.add("loading");
  resultEl.classList.remove("visible");

  try {
    const note = await quickFindByTag(tag);
    if (!note) {
      resultEl.innerHTML = `<span style="color:var(--text-muted)">No note found with tag <strong>${tag}</strong>.</span>`;
    } else {
      resultEl.innerHTML = `
        <strong>🔍 First match for <span class="note-tag ${tagClass(note.tag)}">${(note.tag||"").toUpperCase()}</span></strong><br>
        <strong>${note.title}</strong><br>
        <span style="color:var(--text-muted);font-size:0.8rem">${(note.content||"").slice(0,120)}…</span>`;

      showView("view-notes");
      setTimeout(() => {
        const card = document.querySelector(`.note-card[data-id="${note.id}"]`);
        if (card) {
          document.querySelectorAll(".note-card.highlighted").forEach(c => c.classList.remove("highlighted"));
          card.classList.add("highlighted");
          card.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 200);
    }
    resultEl.classList.add("visible");
  } catch (e) {
    resultEl.innerHTML = `<span style="color:var(--red)">Error: ${e.message}</span>`;
    resultEl.classList.add("visible");
  } finally {
    btn.classList.remove("loading");
  }
}

// ── Smart Search view ─────────────────────────────────────────
on("smart-search-btn", "click", async () => {
  const query = document.getElementById("smart-search-input").value.trim();
  const res   = document.getElementById("smart-search-results");
  if (!query) {
    res.innerHTML = `<p class="ai-msg">Enter a query to search by meaning.</p>`;
    return;
  }
  res.innerHTML = `<p class="ai-msg">⏳ Computing semantic embeddings…</p>`;
  try {
    const results = await smartSearch(query);

    if (!results.length) {
      res.innerHTML = `<p class="ai-msg">No relevant matches found for "<strong>${query}</strong>".</p>`;
      return;
    }

    res.innerHTML = `<p class="ai-msg">Top matches for "<strong>${query}</strong>"</p>`;
    results.forEach(item => {
      const pct = (item.similarity * 100).toFixed(1);
      const quality = item.similarity >= 0.5 ? "sim-high"
                    : item.similarity >= 0.25 ? "sim-mid"
                    : "sim-low";

      const card = document.createElement("div");
      card.className = "smart-result-card";
      card.innerHTML = `
        <div class="sim-row">
          <span class="sim-score ${quality}">${pct}% match</span>
          <span class="sim-tag note-tag ${tagClass(item.tag)}">${(item.tag||"untagged").toUpperCase()}</span>
        </div>
        <strong>${item.title}</strong>
        <p>${item.content.length > 140 ? item.content.slice(0,140)+"…" : item.content}</p>
        <button class="btn-goto-note" data-id="${item.id}">→ View Note</button>
      `;
      card.querySelector(".btn-goto-note").addEventListener("click", () => {
        showView("view-notes");
        setTimeout(() => {
          const noteCard = document.querySelector(`.note-card[data-id="${item.id}"]`);
          if (noteCard) {
            document.querySelectorAll(".note-card.highlighted").forEach(c => c.classList.remove("highlighted"));
            noteCard.classList.add("highlighted");
            noteCard.scrollIntoView({ behavior:"smooth", block:"center" });
          }
        }, 200);
      });
      res.appendChild(card);
    });
  } catch(e) {
    res.innerHTML = `<p style="color:var(--red);font-size:0.82rem">Error: ${e.message}</p>`;
  }
});

document.getElementById("smart-search-btn") && document.getElementById("smart-search-btn").addEventListener("click", () => {});

// ── ChatGPT-style AI Tools ────────────────────────────────────

const chatHistory = [];   // {role, content}[]
let isBotTyping   = false;

function getUserInitial() {
  return (localStorage.getItem("zn_user_name") || "U").charAt(0).toUpperCase();
}

function appendMessage(role, text) {
  const messages = document.getElementById("chat-messages");
  if (!messages) return;

  const msg = document.createElement("div");
  msg.className = `chat-msg ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = role === "user" ? getUserInitial() : "🤖";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";

  // Convert markdown-lite to HTML
  bubble.innerHTML = formatResponse(text);

  msg.appendChild(avatar);
  msg.appendChild(bubble);
  messages.appendChild(msg);
  messages.scrollTop = messages.scrollHeight;
  return bubble;
}

function showTyping() {
  const messages = document.getElementById("chat-messages");
  if (!messages) return null;
  const msg = document.createElement("div");
  msg.className = "chat-msg assistant typing-indicator";
  msg.id = "typing-indicator";
  msg.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-bubble">
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
    </div>`;
  messages.appendChild(msg);
  messages.scrollTop = messages.scrollHeight;
  return msg;
}

function removeTyping() {
  const el = document.getElementById("typing-indicator");
  if (el) el.remove();
}

function formatResponse(text) {
  return text
    .replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/^### (.+)$/gm, "<strong>$1</strong>")
    .replace(/^## (.+)$/gm, "<strong>$1</strong>")
    .replace(/^# (.+)$/gm, "<strong>$1</strong>")
    .replace(/^- (.+)$/gm, "• $1")
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g, "<br>");
}

async function sendChatMessage(message) {
  if (!message.trim() || isBotTyping) return;
  isBotTyping = true;

  // Hide suggestions after first message
  const suggestions = document.getElementById("chat-suggestions");
  if (suggestions) suggestions.style.display = "none";

  // Add user message to UI and history
  appendMessage("user", message);
  chatHistory.push({ role: "user", content: message });

  // Clear input
  const input = document.getElementById("chat-input");
  if (input) { input.value = ""; input.style.height = "auto"; }

  // Disable send button
  const sendBtn = document.getElementById("chat-send-btn");
  if (sendBtn) sendBtn.disabled = true;

  // Show typing indicator
  showTyping();

  try {
    const res = await fetch(`${API_BASE}/ai/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history: chatHistory.slice(-10) }),
    });

    removeTyping();

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      appendMessage("assistant", `Sorry, something went wrong: ${err.detail || res.status}`);
    } else {
      const data = await res.json();
      const reply = data.reply || "I couldn't generate a response.";
      appendMessage("assistant", reply);
      chatHistory.push({ role: "assistant", content: reply });
    }
  } catch (e) {
    removeTyping();
    appendMessage("assistant", `Connection error: ${e.message}. Is the backend running?`);
  } finally {
    isBotTyping = false;
    if (sendBtn) sendBtn.disabled = false;
  }
}

// Wire chat events
on("chat-send-btn", "click", () => {
  const input = document.getElementById("chat-input");
  if (input) sendChatMessage(input.value.trim());
});

on("chat-input", "keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    const input = document.getElementById("chat-input");
    if (input) sendChatMessage(input.value.trim());
  }
});

// Auto-resize textarea
on("chat-input", "input", () => {
  const input = document.getElementById("chat-input");
  if (!input) return;
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 120) + "px";
});

// Suggested prompts
on("chat-suggestions", "click", (e) => {
  const btn = e.target.closest(".suggest-btn");
  if (!btn) return;
  sendChatMessage(btn.dataset.msg);
});

// Clear chat
on("clear-chat-btn", "click", () => {
  chatHistory.length = 0;
  const messages = document.getElementById("chat-messages");
  if (!messages) return;
  messages.innerHTML = `
    <div class="chat-msg assistant">
      <div class="msg-avatar">🤖</div>
      <div class="msg-bubble">
        <p>Chat cleared. How can I help you?</p>
      </div>
    </div>`;
  const suggestions = document.getElementById("chat-suggestions");
  if (suggestions) suggestions.style.display = "flex";
});
// ── Tag Browser — Hardcoded tree structure with filtering + search ───

const CATEGORY_TREE = {
  name: "All Tags",
  tag: "", // empty = show all notes
  children: [
    { 
      name: "Work", 
      tag: "work",
      children: [
        { name: "Standups", tag: "work/standups", children: [] },
        { name: "Retros", tag: "work/retros", children: [] },
      ]
    },
    { 
      name: "Personal", 
      tag: "personal",
      children: [
        { 
          name: "Health", 
          tag: "health",
          children: [
            { name: "Fitness", tag: "health/fitness", children: [] },
          ]
        },
        { name: "Recipes", tag: "recipes", children: [] },
      ]
    },
    { name: "Travel", tag: "travel", children: [] },
  ],
};

/**
 * Renders a single tree node as an <li>.
 * Clicking the tag name:
 *   1. Filters the Dashboard to show matching notes.
 *   2. Pre-fills the Search Notes keyword input so it also acts as a search.
 */
function renderTreeNode(node, allNotes = []) {
  const li = document.createElement("li");
  const hasChildren = node.children && node.children.length > 0;

  const label = document.createElement("span");
  label.className = "tree-label";

  // Expand / collapse arrow for parent nodes
  if (hasChildren) {
    const arr = document.createElement("span");
    arr.className = "tree-arrow";
    arr.textContent = "▼";
    arr.addEventListener("click", e => { 
      e.stopPropagation(); 
      li.classList.toggle("collapsed"); 
    });
    label.appendChild(arr);
  } else {
    const dot = document.createElement("span");
    dot.className = "tree-dot";
    dot.textContent = "•";
    label.appendChild(dot);
  }

  // Tag name — clickable: filter + search
  const text = document.createElement("span");
  text.className = "tree-name";
  
  // Count matching notes for this tag
  const tagVal = node.tag || "";
  let count = 0;
  if (tagVal) {
    count = allNotes.filter(n => {
      if (!n.tag) return false;
      return n.tag.toLowerCase() === tagVal.toLowerCase() || 
             n.tag.toLowerCase().startsWith(tagVal.toLowerCase() + "/");
    }).length;
  } else {
    count = allNotes.length; // "All Tags" shows total
  }
  
  text.textContent = node.name + (count > 0 ? ` (${count})` : "");
  text.title = tagVal ? `Filter by tag: ${tagVal}` : "Show all notes";

  text.addEventListener("click", async e => {
    e.stopPropagation();

    // Highlight active item
    document.querySelectorAll(".tree-name.active").forEach(n => n.classList.remove("active"));
    document.querySelectorAll(".tag-nav-item").forEach(i => i.classList.remove("active"));
    text.classList.add("active");

    const heading = tagVal ? `🏷️ Tag: ${node.name}` : "All Notes";

    // ── 1. Filter Dashboard view ───────────────────────────────
    showView("view-notes");
    try {
      const filtered = await fetchNotes(tagVal);
      renderNotes(filtered, heading);
      // Sync the toolbar filter dropdown
      const filterSel = document.getElementById("filter-tag");
      if (filterSel) filterSel.value = tagVal;
    } catch (err) {
      console.error("Tag browser filter error:", err);
    }

    // ── 2. Pre-fill Search Notes view input ───────────────────
    const kwInput = document.getElementById("keyword-input");
    if (kwInput) kwInput.value = tagVal;

    // ── 3. Clear toolbar search box ───────────────────────────
    const toolbarSearch = document.getElementById("toolbar-search");
    if (toolbarSearch) toolbarSearch.value = "";
  });

  label.appendChild(text);
  li.appendChild(label);

  // Render children recursively
  if (hasChildren) {
    const ul = document.createElement("ul");
    node.children.forEach(child => ul.appendChild(renderTreeNode(child, allNotes)));
    li.appendChild(ul);
  }

  return li;
}

function renderCategoryTree(tree, el, allNotes = []) {
  el.innerHTML = "";
  const ul = document.createElement("ul");
  ul.appendChild(renderTreeNode(tree, allNotes));
  el.appendChild(ul);
}

/**
 * Rebuild the Tag Browser tree with updated note counts.
 * Called after load and after adding a new note.
 */
function buildAndRenderTagTree(notes) {
  const treeEl = document.getElementById("tag-tree");
  if (!treeEl) return;
  renderCategoryTree(CATEGORY_TREE, treeEl, notes);
}

// ── Boot ──────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initTagDropdown();
  loadNotes();
  
  // Wire AI content suggestion buttons
  const contentBtn = document.getElementById("btn-ai-content-suggest");
  if (contentBtn) contentBtn.addEventListener("click", () => getAIContentSuggestions(false));
  
  const applyBtn = document.getElementById("btn-apply-suggestion");
  if (applyBtn) applyBtn.addEventListener("click", applyContentSuggestion);
  
  const regenBtn = document.getElementById("btn-regenerate-suggestion");
  if (regenBtn) regenBtn.addEventListener("click", () => getAIContentSuggestions(true));
  
  const dismissBtn = document.getElementById("ai-content-dismiss");
  if (dismissBtn) dismissBtn.addEventListener("click", dismissContentSuggestion);

  const briefBtn = document.getElementById("btn-brief-suggestion");
  if (briefBtn) briefBtn.addEventListener("click", briefContentSuggestion);
  
  // Wire AI tag suggestion button
  const aiBtn = document.getElementById("btn-ai-suggest");
  if (aiBtn) aiBtn.addEventListener("click", getAITagSuggestions);

  // ── Mobile menu toggle ───────────────────────────────────────
  const hamburger = document.getElementById("mobile-menu-toggle");
  const sidebar   = document.querySelector(".sidebar");
  const overlay   = document.getElementById("sidebar-overlay");

  if (hamburger && sidebar && overlay) {
    const toggleSidebar = () => {
      hamburger.classList.toggle("open");
      sidebar.classList.toggle("open");
      overlay.classList.toggle("active");
    };

    hamburger.addEventListener("click", toggleSidebar);
    overlay.addEventListener("click", toggleSidebar);

    // Close sidebar when nav item clicked on mobile
    document.querySelectorAll(".nav-item").forEach(item => {
      item.addEventListener("click", () => {
        if (window.innerWidth <= 640) {
          hamburger.classList.remove("open");
          sidebar.classList.remove("open");
          overlay.classList.remove("active");
        }
      });
    });

    // Close sidebar when a tag is clicked on mobile
    document.addEventListener("click", (e) => {
      if (window.innerWidth <= 640 &&
          (e.target.closest(".tag-nav-item") || e.target.closest(".tree-name"))) {
        hamburger.classList.remove("open");
        sidebar.classList.remove("open");
        overlay.classList.remove("active");
      }
    });
  }
});

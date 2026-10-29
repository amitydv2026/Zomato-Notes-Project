
// Production: your Render backend URL
// Local dev:  http://127.0.0.1:8000
const API_BASE = "https://zomato-notes-backend.onrender.com";

// Returns headers for JSON requests with JWT Bearer token.
function authHeaders(extra = {}) {
  const token = localStorage.getItem("zn_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...extra,
  };
}

// Returns headers for multipart/FormData requests (no Content-Type —
// the browser sets it automatically with the correct boundary).
function authHeadersMultipart() {
  const token = localStorage.getItem("zn_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

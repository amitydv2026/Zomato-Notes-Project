
// Production: your Render backend URL
// Local dev:  http://127.0.0.1:8000
const API_BASE = "https://zomato-notes-backend.onrender.com";

// Helper: returns the Authorization header for JWT-protected requests.
// Reads the token stored in localStorage after login.
function authHeaders(extra = {}) {
  const token = localStorage.getItem("zn_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...extra,
  };
}

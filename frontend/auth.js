
// ── Redirect if already logged in ─────────────────────────────────────────────
if (localStorage.getItem("zn_user_id")) {
  window.location.replace("index.html");
}

// ── Tab switching ─────────────────────────────────────────────────────────────
const tabLogin  = document.getElementById("tab-login");
const tabSignup = document.getElementById("tab-signup");
const loginForm  = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");

function switchToLogin(successMsg = "") {
  tabLogin.classList.add("active");
  tabSignup.classList.remove("active");
  loginForm.classList.remove("hidden");
  signupForm.classList.add("hidden");
  document.getElementById("login-error").textContent = "";
  if (successMsg) {
    const el = document.getElementById("login-success");
    if (el) { el.textContent = successMsg; el.style.display = "block"; }
  } else {
    const el = document.getElementById("login-success");
    if (el) el.style.display = "none";
  }
}

function switchToSignup() {
  tabSignup.classList.add("active");
  tabLogin.classList.remove("active");
  signupForm.classList.remove("hidden");
  loginForm.classList.add("hidden");
  document.getElementById("signup-error").textContent = "";
  const el = document.getElementById("login-success");
  if (el) el.style.display = "none";
}

tabLogin.addEventListener("click",  () => switchToLogin());
tabSignup.addEventListener("click", () => switchToSignup());

// ── Default tab: Sign Up for first-timers, Sign In for returning users ────────
const isReturning = !!localStorage.getItem("zn_last_email");
if (isReturning) {
  // Pre-fill email for returning users
  const lastEmail = localStorage.getItem("zn_last_email");
  const emailInput = document.getElementById("login-email");
  if (emailInput && lastEmail) emailInput.value = lastEmail;
  switchToLogin();
} else {
  // First-time visitor — show Sign Up first
  switchToSignup();
}

// ── Cross-tab links ───────────────────────────────────────────────────────────
document.getElementById("goto-signup") && document.getElementById("goto-signup").addEventListener("click", (e) => {
  e.preventDefault();
  switchToSignup();
});
document.getElementById("goto-login") && document.getElementById("goto-login").addEventListener("click", (e) => {
  e.preventDefault();
  switchToLogin();
});

// ── Password visibility toggle ────────────────────────────────────────────────
document.querySelectorAll(".toggle-pw").forEach(btn => {
  btn.addEventListener("click", () => {
    const input = document.getElementById(btn.dataset.target);
    input.type = input.type === "password" ? "text" : "password";
    btn.textContent = input.type === "password" ? "👁" : "🙈";
  });
});

// ── Login ─────────────────────────────────────────────────────────────────────
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("login-error");
  errorEl.textContent = "";

  const email    = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  if (!email || !password) {
    errorEl.textContent = "Please enter both email and password.";
    return;
  }

  const btn = document.getElementById("login-btn");
  btn.disabled = true;
  btn.textContent = "Signing in…";
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      errorEl.textContent = data.detail || "Invalid email or password.";
      return;
    }

    const user = await res.json();
    // Save session to localStorage
    localStorage.setItem("zn_user_id",   user.id);
    localStorage.setItem("zn_user_name", user.name);
    localStorage.setItem("zn_user_email", user.email);
    localStorage.setItem("zn_last_email", user.email);

    // Redirect to main app
    window.location.replace("index.html");

  } catch (err) {
    errorEl.textContent = "Could not connect to server. Is the backend running?";
  } finally {
    btn.disabled = false;
    btn.textContent = "Sign In";
  }
});

// ── Signup ────────────────────────────────────────────────────────────────────
signupForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("signup-error");
  errorEl.textContent = "";

  const name     = document.getElementById("signup-name").value.trim();
  const email    = document.getElementById("signup-email").value.trim();
  const password = document.getElementById("signup-password").value;

  if (!name)               { errorEl.textContent = "Name is required."; return; }
  if (!email)              { errorEl.textContent = "Email is required."; return; }
  if (password.length < 8) { errorEl.textContent = "Password must be at least 8 characters."; return; }

  const btn = document.getElementById("signup-btn");
  btn.disabled = true;
  btn.textContent = "Creating account…";

  try {
    const res = await fetch(`${API_BASE}/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      errorEl.textContent = data.detail || "Signup failed. Please try again.";
      return;
    }

    // Account created — switch to login tab with success message
    // Store email so login form is pre-filled
    localStorage.setItem("zn_last_email", data.email);
    document.getElementById("signup-form").reset();
    switchToLogin(`✅ Account created! Please log in with your new credentials.`);
    // Pre-fill email in login form
    const loginEmailEl = document.getElementById("login-email");
    if (loginEmailEl) loginEmailEl.value = data.email;

  } catch (err) {
    errorEl.textContent = "Could not connect to server. Is the backend running?";
  } finally {
    btn.disabled = false;
    btn.textContent = "Create Account";
  }
});

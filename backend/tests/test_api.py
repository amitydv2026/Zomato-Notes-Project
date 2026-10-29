"""
Integration tests for main.py API endpoints.
Uses FastAPI's TestClient with the in-memory SQLite DB override from conftest.

All write/mutate operations now use JWT Bearer authentication.
The `auth_client` fixture (from conftest) provides a pre-authenticated client.
"""

# NOTE: `password` must be >= 8 chars (UserCreate min_length=8).
TEST_PASSWORD = "testpass123"


# ── Health ────────────────────────────────────────────────────────────────────

def test_ping(client):
    res = client.get("/ping")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


# ── Users / Auth ──────────────────────────────────────────────────────────────

def test_create_user_then_login(client):
    res = client.post("/users", json={
        "name": "Amit",
        "email": "amit@test.com",
        "password": TEST_PASSWORD,
    })
    assert res.status_code == 201
    user = res.json()
    assert user["email"] == "amit@test.com"
    user_id = user["id"]

    login = client.post("/auth/login", json={
        "email": "amit@test.com",
        "password": TEST_PASSWORD,
    })
    assert login.status_code == 200
    body = login.json()
    assert body["id"] == user_id
    # JWT fields must be present
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20   # sanity: not empty


def test_create_user_rejects_duplicate_email(client):
    payload = {"name": "Amit", "email": "dup@test.com", "password": TEST_PASSWORD}
    assert client.post("/users", json=payload).status_code == 201
    res = client.post("/users", json=payload)
    assert res.status_code == 409


def test_create_user_rejects_short_password(client):
    res = client.post("/users", json={
        "name": "Short", "email": "short@test.com", "password": "123"
    })
    assert res.status_code == 422


def test_login_wrong_password(client):
    client.post("/users", json={
        "name": "Amit", "email": "wrong@pw.com", "password": TEST_PASSWORD
    })
    res = client.post("/auth/login", json={
        "email": "wrong@pw.com", "password": "not-the-password"
    })
    assert res.status_code == 401


def test_login_unknown_email(client):
    res = client.post("/auth/login", json={
        "email": "nobody@test.com", "password": TEST_PASSWORD
    })
    assert res.status_code == 401


# ── Notes ─────────────────────────────────────────────────────────────────────

def test_create_note_requires_jwt(client):
    """POST /notes without a token must return 401."""
    res = client.post("/notes", json={
        "title": "Orphan note",
        "content": "no token supplied",
        "tag": "work",
    })
    assert res.status_code == 401


def test_create_and_get_note(auth_client):
    """Authenticated user can create a note; owner_id is derived from the JWT."""
    create = auth_client.client.post("/notes", json={
        "title": "Postgres outage runbook",
        "content": "Restart the postgres instance and check connection pool.",
        "tag": "work",
    }, headers=auth_client.headers)
    assert create.status_code == 201
    note = create.json()
    note_id = note["id"]
    assert note["owner_id"] == auth_client.user["id"]
    assert note["owner_name"] == auth_client.user["name"]

    got = auth_client.client.get(f"/notes/{note_id}")
    assert got.status_code == 200
    assert got.json()["title"] == "Postgres outage runbook"


def test_get_note_not_found(client):
    assert client.get("/notes/12345").status_code == 404


def test_list_notes_filters_by_tag(auth_client):
    for tag, title in [("work", "Work note"), ("health", "Health note")]:
        auth_client.client.post("/notes", json={
            "title": title, "content": "body text", "tag": tag,
        }, headers=auth_client.headers)
    res = auth_client.client.get("/notes", params={"tag": "health"})
    assert res.status_code == 200
    notes = res.json()
    assert len(notes) == 1
    assert notes[0]["tag"] == "health"


# ── Search (Part 2) ───────────────────────────────────────────────────────────

def test_search_notes_by_keyword(auth_client):
    auth_client.client.post("/notes", json={
        "title": "Postgres outage runbook",
        "content": "restart the postgres instance",
        "tag": "work",
    }, headers=auth_client.headers)
    res = auth_client.client.get("/notes/search", params={"keyword": "postgres"})
    assert res.status_code == 200
    assert len(res.json()) >= 1
    assert res.json()[0]["score"] > 0


def test_search_notes_requires_params(client):
    res = client.get("/notes/search")
    assert res.status_code == 400


def test_search_notes_sort_by_date(auth_client):
    auth_client.client.post("/notes", json={
        "title": "First", "content": "a", "tag": "work",
    }, headers=auth_client.headers)
    auth_client.client.post("/notes", json={
        "title": "Second", "content": "b", "tag": "work",
    }, headers=auth_client.headers)
    res = auth_client.client.get("/notes/search", params={"sort_by": "date"})
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_lookup_note_by_title(auth_client):
    auth_client.client.post("/notes", json={
        "title": "Alpha runbook",
        "content": "content here",
        "tag": "work",
    }, headers=auth_client.headers)
    res = auth_client.client.get("/notes/lookup", params={"title": "Alpha runbook", "algo": "iterative"})
    assert res.status_code == 200
    assert res.json()["title"] == "Alpha runbook"


def test_lookup_note_not_found(client):
    assert client.get("/notes/lookup", params={"title": "Does Not Exist"}).status_code == 404


def test_quick_find_by_tag(auth_client):
    auth_client.client.post("/notes", json={
        "title": "Tagged note", "content": "body", "tag": "travel",
    }, headers=auth_client.headers)
    res = auth_client.client.get("/notes/quick-find", params={"tag": "travel"})
    assert res.status_code == 200
    assert res.json()["tag"] == "travel"


def test_quick_find_tag_not_found(client):
    assert client.get("/notes/quick-find", params={"tag": "nonexistent"}).status_code == 404


# ── Update / Delete (JWT ownership enforcement) ────────────────────────────────

def _create_second_user_token(client, email="other@test.com"):
    """Helper: register a second user and return their JWT token."""
    client.post("/users", json={
        "name": "Other", "email": email, "password": TEST_PASSWORD
    })
    login = client.post("/auth/login", json={"email": email, "password": TEST_PASSWORD})
    return login.json()["access_token"]


def test_update_note_requires_jwt(auth_client):
    """PUT /notes/{id} without a token returns 401."""
    note = auth_client.client.post("/notes", json={
        "title": "Original", "content": "content", "tag": "work",
    }, headers=auth_client.headers).json()

    res = auth_client.client.put(f"/notes/{note['id']}", json={"title": "Changed"})
    assert res.status_code == 401


def test_update_note_wrong_owner(auth_client):
    """PUT /notes/{id} with a different user's token returns 403."""
    note = auth_client.client.post("/notes", json={
        "title": "Original", "content": "content", "tag": "work",
    }, headers=auth_client.headers).json()

    other_token = _create_second_user_token(auth_client.client)
    res = auth_client.client.put(
        f"/notes/{note['id']}", json={"title": "Changed"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res.status_code == 403


def test_update_note_owner_succeeds(auth_client):
    """PUT /notes/{id} with the owner's token succeeds."""
    note = auth_client.client.post("/notes", json={
        "title": "Original", "content": "content", "tag": "work",
    }, headers=auth_client.headers).json()

    res = auth_client.client.put(
        f"/notes/{note['id']}", json={"title": "Changed"},
        headers=auth_client.headers,
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Changed"


def test_delete_note_requires_jwt(auth_client):
    """DELETE /notes/{id} without a token returns 401."""
    note = auth_client.client.post("/notes", json={
        "title": "To delete", "content": "content", "tag": "work",
    }, headers=auth_client.headers).json()

    res = auth_client.client.delete(f"/notes/{note['id']}")
    assert res.status_code == 401


def test_delete_note_wrong_owner(auth_client):
    """DELETE /notes/{id} with a different user's token returns 403."""
    note = auth_client.client.post("/notes", json={
        "title": "To delete", "content": "content", "tag": "work",
    }, headers=auth_client.headers).json()

    other_token = _create_second_user_token(auth_client.client, email="delother@test.com")
    res = auth_client.client.delete(
        f"/notes/{note['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res.status_code == 403


def test_delete_note_success(auth_client):
    """DELETE /notes/{id} with the owner's token succeeds and note is gone."""
    note = auth_client.client.post("/notes", json={
        "title": "To delete", "content": "content", "tag": "work",
    }, headers=auth_client.headers).json()

    res = auth_client.client.delete(
        f"/notes/{note['id']}",
        headers=auth_client.headers,
    )
    assert res.status_code == 200
    assert auth_client.client.get(f"/notes/{note['id']}").status_code == 404


def test_invalid_token_is_rejected(client, auth_client):
    """A tampered / invalid token returns 401."""
    note = auth_client.client.post("/notes", json={
        "title": "Secure note", "content": "content", "tag": "work",
    }, headers=auth_client.headers).json()

    res = client.delete(
        f"/notes/{note['id']}",
        headers={"Authorization": "Bearer this.is.not.a.valid.token"},
    )
    assert res.status_code == 401

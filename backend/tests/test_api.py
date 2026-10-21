"""
Integration tests for main.py API endpoints.
Uses FastAPI's TestClient with the in-memory SQLite DB override from conftest.
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
    assert login.json()["id"] == user_id


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

def _make_user(client, email="user@test.com"):
    res = client.post("/users", json={
        "name": "Tester", "email": email, "password": TEST_PASSWORD
    })
    return res.json()


def test_create_note_requires_valid_owner(client):
    res = client.post("/notes", json={
        "title": "Orphan note",
        "content": "no owner",
        "tag": "work",
        "owner_id": 999,
    })
    assert res.status_code == 404


def test_create_and_get_note(client):
    user = _make_user(client, email="note@test.com")
    create = client.post("/notes", json={
        "title": "Postgres outage runbook",
        "content": "Restart the postgres instance and check connection pool.",
        "tag": "work",
        "owner_id": user["id"],
    })
    assert create.status_code == 201
    note_id = create.json()["id"]
    assert create.json()["owner_name"] == "Tester"

    got = client.get(f"/notes/{note_id}")
    assert got.status_code == 200
    assert got.json()["title"] == "Postgres outage runbook"


def test_get_note_not_found(client):
    assert client.get("/notes/12345").status_code == 404


def test_list_notes_filters_by_tag(client):
    user = _make_user(client, email="list@test.com")
    for tag, title in [("work", "Work note"), ("health", "Health note")]:
        client.post("/notes", json={
            "title": title, "content": "body text", "tag": tag,
            "owner_id": user["id"],
        })
    res = client.get("/notes", params={"tag": "health"})
    assert res.status_code == 200
    notes = res.json()
    assert len(notes) == 1
    assert notes[0]["tag"] == "health"


# ── Search (Part 2) ───────────────────────────────────────────────────────────

def test_search_notes_by_keyword(client):
    user = _make_user(client, email="search@test.com")
    client.post("/notes", json={
        "title": "Postgres outage runbook",
        "content": "restart the postgres instance",
        "tag": "work",
        "owner_id": user["id"],
    })
    res = client.get("/notes/search", params={"keyword": "postgres"})
    assert res.status_code == 200
    assert len(res.json()) >= 1
    assert res.json()[0]["score"] > 0


def test_search_notes_requires_params(client):
    res = client.get("/notes/search")
    assert res.status_code == 400


def test_search_notes_sort_by_date(client):
    user = _make_user(client, email="sort@test.com")
    client.post("/notes", json={
        "title": "First", "content": "a", "tag": "work", "owner_id": user["id"],
    })
    client.post("/notes", json={
        "title": "Second", "content": "b", "tag": "work", "owner_id": user["id"],
    })
    res = client.get("/notes/search", params={"sort_by": "date"})
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_lookup_note_by_title(client):
    user = _make_user(client, email="lookup@test.com")
    client.post("/notes", json={
        "title": "Alpha runbook",
        "content": "content here",
        "tag": "work",
        "owner_id": user["id"],
    })
    res = client.get("/notes/lookup", params={"title": "Alpha runbook", "algo": "iterative"})
    assert res.status_code == 200
    assert res.json()["title"] == "Alpha runbook"


def test_lookup_note_not_found(client):
    assert client.get("/notes/lookup", params={"title": "Does Not Exist"}).status_code == 404


def test_quick_find_by_tag(client):
    user = _make_user(client, email="quickfind@test.com")
    client.post("/notes", json={
        "title": "Tagged note", "content": "body", "tag": "travel",
        "owner_id": user["id"],
    })
    res = client.get("/notes/quick-find", params={"tag": "travel"})
    assert res.status_code == 200
    assert res.json()["tag"] == "travel"


def test_quick_find_tag_not_found(client):
    assert client.get("/notes/quick-find", params={"tag": "nonexistent"}).status_code == 404


# ── Update / Delete (permissions) ─────────────────────────────────────────────

def test_update_note_owner_only(client):
    user = _make_user(client, email="upd@test.com")
    note = client.post("/notes", json={
        "title": "Original", "content": "content", "tag": "work",
        "owner_id": user["id"],
    }).json()

    # No x-user-id header → 401
    assert client.put(f"/notes/{note['id']}", json={"title": "Changed"}).status_code == 401

    # Wrong owner → 403
    res = client.put(
        f"/notes/{note['id']}", json={"title": "Changed"},
        headers={"x-user-id": "999"},
    )
    assert res.status_code == 403

    # Correct owner → 200
    res = client.put(
        f"/notes/{note['id']}", json={"title": "Changed"},
        headers={"x-user-id": str(user["id"])},
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Changed"


def test_delete_note_requires_token(client):
    user = _make_user(client, email="del@test.com")
    note = client.post("/notes", json={
        "title": "To delete", "content": "content", "tag": "work",
        "owner_id": user["id"],
    }).json()

    # No x-token header → 401 (verify_token runs first)
    res = client.delete(
        f"/notes/{note['id']}", headers={"x-user-id": str(user["id"])}
    )
    assert res.status_code == 401


def test_delete_note_wrong_token(client):
    user = _make_user(client, email="deltok@test.com")
    note = client.post("/notes", json={
        "title": "To delete", "content": "content", "tag": "work",
        "owner_id": user["id"],
    }).json()

    res = client.delete(
        f"/notes/{note['id']}",
        headers={"x-user-id": str(user["id"]), "x-token": "wrong-token"},
    )
    assert res.status_code == 403


def test_delete_note_success(client):
    user = _make_user(client, email="delok@test.com")
    note = client.post("/notes", json={
        "title": "To delete", "content": "content", "tag": "work",
        "owner_id": user["id"],
    }).json()

    res = client.delete(
        f"/notes/{note['id']}",
        headers={
            "x-user-id": str(user["id"]),
            "x-token": "test-secret",   # matches SECRET_TOKEN set in conftest
        },
    )
    assert res.status_code == 200
    assert client.get(f"/notes/{note['id']}").status_code == 404

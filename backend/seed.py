"""
Seed the database with demo data for all three parts.
Run once:  python seed.py

PostgreSQL note: after inserting rows with explicit IDs we reset the sequences
so that subsequent auto-increment inserts don't collide.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from database import engine, SessionLocal, Base
import models  # noqa: F401 — needed so Base knows about the tables
from ranking_dataset import RANKING_DATASET
from ai_sample_notes import AI_SAMPLE_NOTES

# ── Seed data ─────────────────────────────────────────────────────────────────

SEED_USERS = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "password": "alicepass123"},
    {"id": 2, "name": "Bob",   "email": "bob@example.com",   "password": "bobpass123"},
]

SEED_NOTES = [
    {"id": 1,  "owner_id": 1, "title": "Standup Summary",   "tag": "work",
     "content": "Discussed sprint progress, blockers on the payments API integration, and the plan for the demo on Friday."},
    {"id": 2,  "owner_id": 1, "title": "Sprint Retro Notes", "tag": "work",
     "content": "Retro highlighted communication gaps between frontend and backend teams and agreed on daily syncs going forward."},
    {"id": 3,  "owner_id": 2, "title": "One on One",         "tag": "work",
     "content": "Quick check-in, no blockers, discussed career growth goals for next quarter."},
    {"id": 4,  "owner_id": 1, "title": "Morning Run",        "tag": "health",
     "content": "Ran 5km along the river trail before breakfast, felt great."},
    {"id": 5,  "owner_id": 2, "title": "Doctor Visit",       "tag": "health",
     "content": "Annual checkup went well, blood pressure normal, scheduled next visit in six months."},
    {"id": 6,  "owner_id": 1, "title": "Pasta Recipe",       "tag": "recipes",
     "content": "Boil pasta, saute garlic in olive oil, add tomatoes, basil, and a pinch of chili flakes."},
    {"id": 7,  "owner_id": 2, "title": "Smoothie Recipe",    "tag": "recipes",
     "content": "Blend banana, spinach, almond milk, and a spoon of peanut butter for breakfast."},
    {"id": 8,  "owner_id": 1, "title": "Flight Booking",     "tag": "travel",
     "content": "Booked a round trip flight for the December vacation, window seat confirmed."},
    {"id": 9,  "owner_id": 2, "title": "Random Thought",     "tag": "random",
     "content": "Maybe the library needs a better recommendation system based on reading history."},
    {"id": 10, "owner_id": 1, "title": "Quote To Remember",  "tag": "random",
     "content": "Done is better than perfect, keep shipping."},
]


def _reset_sequences(db):
    """
    After inserting rows with explicit IDs, reset PostgreSQL sequences so
    auto-increment picks up from max(id) + 1.
    This prevents 'duplicate key value violates unique constraint' on future inserts.
    """
    db.execute(text(
        "SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"
    ))
    db.execute(text(
        "SELECT setval('notes_id_seq', (SELECT MAX(id) FROM notes))"
    ))
    db.commit()


def seed():
    # Create all tables (safe to run multiple times — CREATE TABLE IF NOT EXISTS)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ── Users ──────────────────────────────────────────────────────────
        for u in SEED_USERS:
            existing = db.query(models.User).filter_by(id=u["id"]).first()
            if not existing:
                db.add(models.User(**u))
        db.commit()

        # ── Core notes (part 1) ────────────────────────────────────────────
        for n in SEED_NOTES:
            existing = db.query(models.Note).filter_by(id=n["id"]).first()
            if not existing:
                db.add(models.Note(**n))
        db.commit()

        # Reset sequences so future auto-inserts start above max explicit id
        _reset_sequences(db)

        # ── Ranking dataset (part 2) — owner_id=1, tag="kb-demo" ──────────
        for item in RANKING_DATASET:
            existing = db.query(models.Note).filter_by(
                title=item["title"], tag="kb-demo"
            ).first()
            if not existing:
                db.add(models.Note(
                    title=item["title"],
                    content=item["content"],
                    tag="kb-demo",
                    owner_id=1,
                ))
        db.commit()

        # ── AI sample notes (part 3) — owner_id=2, tag="ai-demo" ──────────
        for item in AI_SAMPLE_NOTES:
            existing = db.query(models.Note).filter_by(
                title=item["title"], tag="ai-demo"
            ).first()
            if not existing:
                db.add(models.Note(
                    title=item["title"],
                    content=item["content"],
                    tag="ai-demo",
                    owner_id=2,
                ))
        db.commit()

        print("✅  Database seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

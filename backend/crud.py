from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import models
import schemas


# ── Users ─────────────────────────────────────────────────────────────────────

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(
        name=user.name,
        email=user.email,
        password=user.password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


# ── Notes ─────────────────────────────────────────────────────────────────────

def create_note(db: Session, note: schemas.NoteCreate) -> models.Note:
    db_note = models.Note(
        title=note.title,
        content=note.content,
        tag=note.tag,
        owner_id=note.owner_id,
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def get_notes(db: Session, tag: Optional[str] = None) -> List[models.Note]:
    q = db.query(models.Note)
    if tag:
        q = q.filter(models.Note.tag == tag)
    return q.all()


def get_note(db: Session, note_id: int) -> Optional[models.Note]:
    return db.query(models.Note).filter(models.Note.id == note_id).first()


def update_note(
    db: Session, note_id: int, update: schemas.NoteUpdate
) -> Optional[models.Note]:
    db_note = get_note(db, note_id)
    if not db_note:
        return None
    if update.title is not None:
        db_note.title = update.title
    if update.content is not None:
        db_note.content = update.content
    if update.tag is not None:
        db_note.tag = update.tag
    db.commit()
    db.refresh(db_note)
    return db_note


def delete_note(db: Session, note_id: int) -> bool:
    db_note = get_note(db, note_id)
    if not db_note:
        return False
    db.delete(db_note)
    db.commit()
    return True


def get_all_notes_ordered_by_title(db: Session) -> List[models.Note]:
    """Returns notes ordered by title ASC case-insensitively — must match
    the binary search algorithm which compares titles with .lower()."""
    from sqlalchemy import func
    return db.query(models.Note).order_by(func.lower(models.Note.title).asc()).all()


# ── Raw-SQL reporting ─────────────────────────────────────────────────────────

def report_tag_summary(db: Session):
    """Tags with more than 1 note, using raw SQL GROUP BY / HAVING."""
    sql = text(
        """
        SELECT tag, COUNT(*) AS count
        FROM notes
        WHERE tag IS NOT NULL
        GROUP BY tag
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        """
    )
    rows = db.execute(sql).fetchall()
    return [{"tag": row[0], "count": row[1]} for row in rows]


def report_long_notes(db: Session):
    """Notes whose content length is above average, using a raw SQL subquery."""
    sql = text(
        """
        SELECT id, title, content, tag, owner_id, created_at
        FROM notes
        WHERE LENGTH(content) > (SELECT AVG(LENGTH(content)) FROM notes)
        ORDER BY LENGTH(content) DESC
        """
    )
    rows = db.execute(sql).fetchall()
    return [
        {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "tag": row[3],
            "owner_id": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


def report_user_notes(db: Session):
    """JOIN between User and Note — user name alongside their total note count."""
    sql = text(
        """
        SELECT u.id, u.name, COUNT(n.id) AS total_notes
        FROM users u
        LEFT JOIN notes n ON n.owner_id = u.id
        GROUP BY u.id, u.name
        ORDER BY total_notes DESC
        """
    )
    rows = db.execute(sql).fetchall()
    return [{"user_id": row[0], "name": row[1], "total_notes": row[2]} for row in rows]

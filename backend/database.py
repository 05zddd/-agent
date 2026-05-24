from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from .models import SessionLocal, ChatHistory, TripRecord, DocumentRecord


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_chat_message(session_id: str, role: str, content: str):
    db = SessionLocal()
    try:
        msg = ChatHistory(session_id=session_id, role=role, content=content)
        db.add(msg)
        db.commit()
    finally:
        db.close()


def get_all_sessions() -> list[dict]:
    """Get list of all distinct sessions with their latest message."""
    db = SessionLocal()
    try:
        from sqlalchemy import func, distinct
        sessions = (
            db.query(
                ChatHistory.session_id,
                func.min(ChatHistory.created_at).label("first_at"),
                func.count(ChatHistory.id).label("msg_count"),
            )
            .group_by(ChatHistory.session_id)
            .order_by(func.min(ChatHistory.created_at).desc())
            .all()
        )
        return [
            {"session_id": s.session_id, "msg_count": s.msg_count}
            for s in sessions
        ]
    finally:
        db.close()


def get_chat_history(session_id: str, limit: int = 20) -> list[dict]:
    db = SessionLocal()
    try:
        msgs = (
            db.query(ChatHistory)
            .filter(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        return [{"role": m.role, "content": m.content} for m in reversed(msgs)]
    finally:
        db.close()


def save_trip_record(session_id: str, city: str, days: int, preferences: str, plan_json: str):
    db = SessionLocal()
    try:
        record = TripRecord(
            session_id=session_id,
            city=city,
            days=days,
            preferences=preferences,
            plan_json=plan_json,
        )
        db.add(record)
        db.commit()
    finally:
        db.close()


def save_document_record(session_id: str, filename: str, file_type: str, file_path: str, chunks_count: int):
    db = SessionLocal()
    try:
        record = DocumentRecord(
            session_id=session_id,
            filename=filename,
            file_type=file_type,
            file_path=file_path,
            chunks_count=chunks_count,
        )
        db.add(record)
        db.commit()
    finally:
        db.close()

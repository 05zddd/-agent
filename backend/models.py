from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


# --- Request models ---

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class TripPlanRequest(BaseModel):
    city: str
    days: int = Field(ge=1, le=14)
    preferences: str = ""
    start_date: Optional[str] = None


class DocumentQuestionRequest(BaseModel):
    question: str
    session_id: str = "default"


# --- Response models ---

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    tool_calls: list[str] = []


class WeatherResponse(BaseModel):
    city: str
    weather: str
    temperature: str
    humidity: str
    wind: str
    forecast: list[dict] = []


class TripDay(BaseModel):
    day: int
    morning: str
    afternoon: str
    evening: str
    notes: str


class TripPlanResponse(BaseModel):
    city: str
    days: int
    schedule: list[TripDay]
    weather_forecast: list[dict] = []
    tips: list[str] = []


class DocumentInfo(BaseModel):
    filename: str
    file_type: str
    size_bytes: int
    chunks_count: int
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    doc_info: Optional[DocumentInfo] = None


# --- DB models (SQLAlchemy) ---

from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True)
    role = Column(String(16))  # user / assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class TripRecord(Base):
    __tablename__ = "trip_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True)
    city = Column(String(64))
    days = Column(Integer)
    preferences = Column(Text, default="")
    plan_json = Column(Text)  # JSON string of trip plan
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True)
    filename = Column(String(256))
    file_type = Column(String(16))
    file_path = Column(String(512))
    chunks_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

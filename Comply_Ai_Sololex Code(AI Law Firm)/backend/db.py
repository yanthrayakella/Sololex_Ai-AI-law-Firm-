import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    company = Column(String, default="")
    subscription_tier = Column(String, default="basic")  # basic | pro
    wechat_openid = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    contracts = relationship("Contract", back_populates="user")
    alerts = relationship("Alert", back_populates="user")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # employment, supplier, lease, service
    file_path = Column(String, nullable=False)
    clauses_json = Column(Text, default="[]")
    risk_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="contracts")
    alerts = relationship("Alert", back_populates="contract")


class Regulation(Base):
    __tablename__ = "regulations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    publish_date = Column(String, default="")
    full_text = Column(Text, default="")
    parsed_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=True)
    regulation_id = Column(String, ForeignKey("regulations.id"), nullable=True)
    severity = Column(String, default="LOW")
    title = Column(String, nullable=False)
    message = Column(Text, default="")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="alerts")
    contract = relationship("Contract", back_populates="alerts")


class UpdatedContract(Base):
    __tablename__ = "updated_contracts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    original_contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    updated_file_path = Column(String, nullable=False)
    changes_summary = Column(Text, default="")
    subscription_tier = Column(String, default="basic")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ScraperSnapshot(Base):
    """Track content fingerprints per source URL for NEW/UPDATED detection."""

    __tablename__ = "scraper_snapshots"

    source_url = Column(String, primary_key=True)
    content_hash = Column(String, default="")
    last_title = Column(String, default="")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def clauses_json_load(raw: str) -> list[dict[str, Any]]:
    try:
        return json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []


def clauses_json_dump(clauses: list[dict[str, Any]]) -> str:
    return json.dumps(clauses, ensure_ascii=False)

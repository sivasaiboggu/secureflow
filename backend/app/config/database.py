from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

import socket
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

db_url = settings.DATABASE_URL

is_postgres_reachable = False
if "localhost" in db_url or "127.0.0.1" in db_url or "::1" in db_url:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(("127.0.0.1", 5432))
        s.close()
        is_postgres_reachable = True
    except Exception:
        is_postgres_reachable = False
elif "db" in db_url:
    is_postgres_reachable = True
else:
    is_postgres_reachable = True

if not is_postgres_reachable:
    # Local fallback to SQLite database
    db_url = "sqlite:///./secureflow.db"

if "sqlite" in db_url:
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        db_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        echo=settings.DEBUG
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

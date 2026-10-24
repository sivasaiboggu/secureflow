from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

from sqlalchemy.engine import make_url

# Never probe a hardcoded port or silently switch data stores on an outage.
# SQLAlchemy connects when a session is used; connection failures must surface
# against the configured database rather than an unrelated SQLite file.
db_url = settings.DATABASE_URL
if make_url(db_url).get_backend_name() == "sqlite":
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

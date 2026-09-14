import logging
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings

logger = logging.getLogger("fraudlens.database")


def get_engine():
    """Build optimized SQLAlchemy engine with connection pooling and fast SQLite PRAGMAs."""
    if "sqlite" in settings.DATABASE_URL:
        eng = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=settings.DB_ECHO,
        )
    else:
        try:
            eng = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                connect_args={"connect_timeout": 1},
                echo=settings.DB_ECHO,
            )
            with eng.connect():
                pass
        except Exception as exc:
            logger.warning(
                "PostgreSQL unreachable at %s (%s). Using local SQLite database (fraud_detection.db).",
                settings.DATABASE_URL,
                exc,
            )
            fallback_url = "sqlite:///./fraud_detection.db"
            eng = create_engine(
                fallback_url,
                connect_args={"check_same_thread": False},
                echo=settings.DB_ECHO,
            )

    # Attach fast PRAGMAs for SQLite engines to boost concurrent read/write speed
    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if "sqlite" in str(eng.url):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
            finally:
                cursor.close()

    return eng


engine = get_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding transactional database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


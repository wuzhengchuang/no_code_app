from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
    max_overflow=10,
    pool_size=5,
    connect_args={"init_command": "SET time_zone = '+00:00'"},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

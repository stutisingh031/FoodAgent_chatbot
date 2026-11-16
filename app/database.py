
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings
from app.logger import logger


# Create the SQLAlchemy engine.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
)


# Create a factory that generates database sessions.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# Base class inherited by all SQLAlchemy models.
class Base(DeclarativeBase):
    pass


# Provide a database session and always close it.
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# Check whether the database is reachable.
def check_database_connection() -> bool:
    from sqlalchemy import text

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("MySQL connection successful")
        return True

    except Exception:
        logger.exception("MySQL connection failed")
        return False

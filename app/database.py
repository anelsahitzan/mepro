import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("sellerai.database")

def create_db_engine():
    try:
        eng = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 3}
        )
        with eng.connect() as conn:
            pass
        logger.info(f"🐘 PostgreSQL дерекқорына сәтті қосылды: {settings.POSTGRES_DB}")
        return eng
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL қосылуы сәтсіз болды ({e}). Резервтік SQLite базасы (sellerai.db) іске қосылды.")
        sqlite_url = "sqlite:///./sellerai.db"
        return create_engine(sqlite_url, connect_args={"check_same_thread": False})

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

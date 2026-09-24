import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("sellerai.database")

PROJECT_DIR = r"c:\Users\User\Desktop\analytics"
DB_PATH = os.path.join(PROJECT_DIR, "sellerai.db")

sqlite_url = f"sqlite:///{DB_PATH.replace(chr(92), '/')}"
logger.info(f"💾 Дерекқор: {sqlite_url}")

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


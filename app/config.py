import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SellerAI Analytics API"
    VERSION: str = "1.0.0"
    
    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "seller_admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "secure_password123")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "sellerai_db")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # AI & Telegram
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

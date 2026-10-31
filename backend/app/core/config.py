from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "ConceptIQ"
    API_V1_STR: str = "/api/v1"
    
    # SQLite fallback
    DATABASE_URL: str = "sqlite:///./conceptiq.db"
    
    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "conceptiq"
    
    # LLM Settings (for Phase 2, strictly optional in Phase 1)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "fallback"  # 'gemini', 'openai', or 'fallback'
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()

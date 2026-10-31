from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "ConceptIQ"
    API_V1_STR: str = "/api/v1"
    
    # SQLite with WAL mode by default
    DATABASE_URL: str = "sqlite:///./conceptiq.db"
    
    # LLM Settings (for Phase 2, strictly optional in Phase 1)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "fallback"  # 'gemini', 'openai', or 'fallback'
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()

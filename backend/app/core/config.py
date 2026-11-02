from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Job Market Skill Trend Analyzer"
    secret_key: str = "dev-only-change-me"
    access_token_expire_minutes: int = 1440
    database_url: str = "sqlite:///./jobmarket.db"
    cors_origins: str = "http://localhost:5173"
    admin_email: str = "admin@example.com"
    admin_password: str = "Admin123!"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

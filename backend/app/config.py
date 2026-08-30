from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./helpdesk.db"
    jwt_secret_key: str = "dev-secret-key-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"

    # Mount point for the API routes. Empty when the API has its own hostname
    # (Render); "/api" when it is served from the same domain as the frontend
    # through CloudFront, which removes cross-origin requests entirely.
    api_prefix: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("api_prefix")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        # Accept "api", "/api" or "/api/" alike. FastAPI asserts on a prefix
        # that lacks a leading slash or carries a trailing one, and a deploy
        # is a bad place to discover that.
        value = value.strip().strip("/")
        return f"/{value}" if value else ""

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Render/Heroku-style Postgres URLs use the "postgres://" scheme,
        # which SQLAlchemy 2.x no longer accepts.
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql://", 1)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

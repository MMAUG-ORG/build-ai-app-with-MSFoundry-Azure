"""Application configuration."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Foundry
    foundry_project_endpoint: str
    foundry_agent_id: str = ""
    foundry_model_deployment: str = "gpt-4o-mini"

    # Postgres
    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str = "support"
    postgres_user: str
    postgres_password: str = ""
    postgres_sslmode: str = "require"

    # Storage
    storage_account_name: str
    storage_container: str = "attachments"

    # API
    cors_origins: str = "*"

    @property
    def database_url(self) -> str:
        pwd = f":{self.postgres_password}" if self.postgres_password else ""
        return (
            f"postgresql+asyncpg://{self.postgres_user}{pwd}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

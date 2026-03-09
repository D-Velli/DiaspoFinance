from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "DiaspoFinance"
    API_VERSION: str = "v1"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/diaspofinance"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Clerk
    CLERK_JWKS_URL: str = ""
    CLERK_WEBHOOK_SECRET: str = ""

    # Plafonds reglementaires — JAMAIS en DB mutable
    MAX_CONTRIBUTION_CENTS: int = 100_000  # 1 000 CAD/transaction
    MAX_MONTHLY_GROUP_CENTS: int = 300_000  # 3 000 CAD/mois/groupe
    MAX_TONTINES_PER_USER: int = 10
    MAX_MEMBERS_PER_TONTINE: int = 20
    MAX_HANDS_PER_MEMBER: int = 2

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

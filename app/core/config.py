from __future__ import annotations

import json

from pydantic import AliasChoices, BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SQLITE_DEFAULT = "sqlite+aiosqlite:///./var/cmep.db"

# Placeholder secrets that must never be accepted in a non-development environment.
_FORBIDDEN_PROD_SECRETS = {
    "",
    "secret",
    "changeme",
    "change-me",
    "change-me-jwt-secret",
    "change-me-to-a-long-random-value",
    "change-me-super-secret-key",
    "test-secret-key",
    "test-secret-key-min-32-chars-long-ok",
    "ci-test-secret-key-min-32-chars-long-ok",
}

MIN_PROD_SECRET_LENGTH = 32


class JWTSettings(BaseModel):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    secret: str = ""
    expire_minutes: int = 60

    def model_post_init(self, __context) -> None:
        if not self.secret:
            object.__setattr__(self, "secret", self.secret_key)


class RedisSettings(BaseModel):
    url: str = "memory://"
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    enabled: bool = False


class RateLimitSettings(BaseModel):
    enabled: bool = False
    limit: int = 10
    period: int = 60
    requests: int = 100
    window_seconds: int = 60


class DatabaseSettings(BaseModel):
    url: str = SQLITE_DEFAULT
    async_url: str = SQLITE_DEFAULT
    echo: bool = False
    pool_size: int = 5
    pool_pre_ping: bool = True

    def model_post_init(self, __context) -> None:
        if not self.async_url:
            object.__setattr__(self, "async_url", self.url)


def _is_placeholder_db_value(raw: str | None) -> bool:
    value = str(raw or "").strip()
    return (
        not value
        or "{" in value
        or "}" in value
        or "POSTGRES_" in value
        or value.lower() in {"none", "null", "undefined"}
    )


def _normalize_database_url(raw: str) -> str:
    value = raw.strip()

    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+asyncpg://", 1)

    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+asyncpg://", 1)

    if value.startswith("sqlite:///"):
        return value.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = "CMEP Platform"
    app_version: str = "0.1.0"
    app_description: str = "CMEP - Platform for circular materials exchange"

    app_env: str = Field(default="development", alias="APP_ENV")
    # None = odvodit z prostredia (v produkcii bezpecne False); explicitna hodnota vzdy vyhra.
    DEBUG: bool | None = Field(default=None, validation_alias=AliasChoices("DEBUG", "APP_DEBUG"))
    ENABLE_PUBLIC_DOCS: bool | None = None
    ENABLE_METRICS: bool = False
    METRICS_ALLOWED_IPS: str = "127.0.0.1,::1,localhost"
    PLATFORM_ADMIN_EMAILS: str = "admin@cmep.dev"
    ROOT_PATH: str = ""

    HOST: str = Field(default="0.0.0.0", validation_alias=AliasChoices("HOST", "APP_HOST"))
    PORT: int = Field(default=8001, validation_alias=AliasChoices("PORT", "APP_PORT"))

    CORS_ORIGINS: list[str] | str = Field(
        default_factory=lambda: [
            "http://127.0.0.1:3001",
            "http://localhost:3001",
        ],
        validation_alias=AliasChoices("CORS_ORIGINS", "CORS_ALLOWED_ORIGINS"),
    )

    DATABASE_URL: str = SQLITE_DEFAULT

    REDIS_URL: str = ""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    JWT_SECRET_KEY: str = Field(validation_alias=AliasChoices("JWT_SECRET_KEY", "JWT_SECRET"))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    # Volitelne sekundove varianty z .env.example; ak su nastavene, maju prednost.
    JWT_ACCESS_TTL_SECONDS: int | None = None
    JWT_REFRESH_TTL_SECONDS: int | None = None

    RATE_LIMIT_ENABLED: bool | None = None

    jwt: JWTSettings | None = None
    redis: RedisSettings = Field(default_factory=RedisSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    database: DatabaseSettings | None = None

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:3001/api/auth/callback/google"
    NEXT_PUBLIC_API_URL: str = "http://127.0.0.1:8001"
    NEXT_PUBLIC_GOOGLE_CLIENT_ID: str = ""

    FRONTEND_URL: str = "https://waste-platform-web.onrender.com"
    EMAIL_FROM: str = Field(default="", validation_alias=AliasChoices("EMAIL_FROM", "EMAIL"))
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = Field(
        default="", validation_alias=AliasChoices("SMTP_USERNAME", "SMTP_USER")
    )
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"development", "dev", "local", "test"}

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, value):
        if value is None or value == "":
            return ["http://127.0.0.1:3001", "http://localhost:3001"]
        if isinstance(value, list):
            return value

        text = str(value).strip()
        if text.startswith("["):
            return json.loads(text)

        return [item.strip() for item in text.split(",") if item.strip()]

    def model_post_init(self, __context) -> None:
        is_development = self.is_development

        # --- Bezpecne defaulty pre produkciu (v development ostava povodne spravanie). ---
        if self.DEBUG is None:
            object.__setattr__(self, "DEBUG", is_development)
        if self.ENABLE_PUBLIC_DOCS is None:
            object.__setattr__(self, "ENABLE_PUBLIC_DOCS", is_development)
        if self.RATE_LIMIT_ENABLED is not None:
            object.__setattr__(
                self,
                "rate_limit",
                self.rate_limit.model_copy(update={"enabled": bool(self.RATE_LIMIT_ENABLED)}),
            )

        # --- JWT secret: v produkcii nesmie byt prazdny ani placeholder. ---
        raw_secret = str(self.JWT_SECRET_KEY or "").strip()
        if not raw_secret:
            raise ValueError(
                "JWT_SECRET_KEY is required (set JWT_SECRET_KEY or JWT_SECRET in the environment)."
            )
        if not is_development:
            if raw_secret.lower() in _FORBIDDEN_PROD_SECRETS:
                raise ValueError(
                    "JWT_SECRET_KEY is a known placeholder. Refusing to start outside development."
                )
            if len(raw_secret) < MIN_PROD_SECRET_LENGTH:
                raise ValueError(
                    f"JWT_SECRET_KEY must be at least {MIN_PROD_SECRET_LENGTH} characters "
                    "outside development."
                )
        object.__setattr__(self, "JWT_SECRET_KEY", raw_secret)

        # --- DATABASE_URL: v produkcii pozaduj realny Postgres, ziadny tichy SQLite fallback. ---
        raw_db = str(self.DATABASE_URL or "").strip()

        if _is_placeholder_db_value(raw_db):
            if is_development:
                database_url = SQLITE_DEFAULT
            else:
                raise ValueError(
                    "DATABASE_URL is missing or invalid for non-development environment."
                )
        else:
            database_url = _normalize_database_url(raw_db)

        if not is_development and database_url.startswith("sqlite"):
            raise ValueError(
                "SQLite is not allowed outside development. Set DATABASE_URL to PostgreSQL."
            )

        object.__setattr__(self, "DATABASE_URL", database_url)
        object.__setattr__(
            self,
            "database",
            DatabaseSettings(
                url=database_url,
                async_url=database_url,
            ),
        )

        # --- Volitelne sekundove TTL varianty maju prednost pred minutovymi. ---
        access_minutes = self.ACCESS_TOKEN_EXPIRE_MINUTES
        if self.JWT_ACCESS_TTL_SECONDS:
            access_minutes = max(1, int(self.JWT_ACCESS_TTL_SECONDS) // 60)

        refresh_days = self.REFRESH_TOKEN_EXPIRE_DAYS
        if self.JWT_REFRESH_TTL_SECONDS:
            refresh_days = max(1, int(self.JWT_REFRESH_TTL_SECONDS) // 86400)

        if self.jwt is None:
            object.__setattr__(
                self,
                "jwt",
                JWTSettings(
                    secret_key=self.JWT_SECRET_KEY,
                    secret=self.JWT_SECRET_KEY,
                    algorithm=self.JWT_ALGORITHM,
                    access_token_expire_minutes=access_minutes,
                    expire_minutes=access_minutes,
                    refresh_token_expire_days=refresh_days,
                ),
            )

        if not is_development and "*" in self.cors_origin_list():
            raise ValueError("CORS_ORIGINS must not contain a wildcard outside development.")

        redis_url = str(self.REDIS_URL or "").strip()
        object.__setattr__(
            self,
            "redis",
            self.redis.model_copy(
                update={
                    "url": redis_url or self.redis.url,
                    "host": str(self.REDIS_HOST or "") or self.redis.host,
                    "port": int(self.REDIS_PORT),
                    "db": int(self.REDIS_DB),
                    "enabled": bool(redis_url),
                }
            ),
        )

    def cors_origin_list(self) -> list[str]:
        value = self.CORS_ORIGINS
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str) and value.strip():
            return [item.strip() for item in value.split(",") if item.strip()]
        return []

    # --- Daily matching job ---
    MATCHING_ENABLED: bool = Field(default=False)
    MATCHING_HOUR: int = Field(default=3)  # 3:00 ráno
    MATCHING_MINUTE: int = Field(default=0)
    MATCHING_MIN_SCORE: int = Field(default=60)  # minimálne skóre pre notifikáciu
    MATCHING_MAX_PER_COMPANY: int = Field(default=5)
    MATCHING_LOOKBACK_DAYS: int = Field(default=7)


settings = Settings()

from __future__ import annotations

import json

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SQLITE_DEFAULT = "sqlite+aiosqlite:///./var/cmep.db"


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
    DEBUG: bool = True
    ENABLE_PUBLIC_DOCS: bool = True
    ENABLE_METRICS: bool = False
    METRICS_ALLOWED_IPS: str = "127.0.0.1,::1,localhost"
    PLATFORM_ADMIN_EMAILS: str = "admin@cmep-bootstrap.dev"
    ROOT_PATH: str = ""

    HOST: str = "0.0.0.0"
    PORT: int = 8001

    CORS_ORIGINS: list[str] | str = Field(
        default_factory=lambda: [
            "http://127.0.0.1:3001",
            "http://localhost:3001",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    DATABASE_URL: str = SQLITE_DEFAULT

    REDIS_URL: str = ""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    jwt: JWTSettings | None = None
    redis: RedisSettings = Field(default_factory=RedisSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    database: DatabaseSettings | None = None

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:3001/api/auth/callback/google"
    NEXT_PUBLIC_API_URL: str = "http://127.0.0.1:8001"
    NEXT_PUBLIC_GOOGLE_CLIENT_ID: str = ""

    EMAIL_FROM: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
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
        raw_db = str(self.DATABASE_URL or "").strip()

        if _is_placeholder_db_value(raw_db):
            if self.is_development:
                database_url = SQLITE_DEFAULT
            else:
                raise ValueError(
                    "DATABASE_URL is missing or invalid for non-development environment."
                )
        else:
            database_url = _normalize_database_url(raw_db)

        object.__setattr__(self, "DATABASE_URL", database_url)
        object.__setattr__(
            self,
            "database",
            DatabaseSettings(
                url=database_url,
                async_url=database_url,
            ),
        )

        if self.jwt is None:
            object.__setattr__(
                self,
                "jwt",
                JWTSettings(
                    secret_key=self.JWT_SECRET_KEY,
                    secret=self.JWT_SECRET_KEY,
                    algorithm=self.JWT_ALGORITHM,
                    access_token_expire_minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES,
                    expire_minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES,
                    refresh_token_expire_days=self.REFRESH_TOKEN_EXPIRE_DAYS,
                ),
            )

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


settings = Settings()

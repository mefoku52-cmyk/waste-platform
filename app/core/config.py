from __future__ import annotations

from typing import List, Union

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class JWTSettings(BaseModel):
    secret_key: str = "cmep-dev-change-me-to-at-least-32-chars-long-secret"
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
    enabled: bool = False  # Termux: vypnuté
    limit: int = 10
    period: int = 60
    requests: int = 100
    window_seconds: int = 60


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Circular Materials Exchange Platform API"
    app_version: str = "0.1.0"
    app_description: str = "CMEP - Platform for circular materials exchange"

    APP_ENV: str = "development"
    DEBUG: bool = True
    ENABLE_PUBLIC_DOCS: bool = True
    ROOT_PATH: str = ""

    HOST: str = "0.0.0.0"
    PORT: int = 8001

    CORS_ORIGINS: Union[List[str], str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:3001",
            "http://localhost:3001",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    DATABASE_URL: str = "sqlite+aiosqlite:///./var/cmep.db"

    JWT_SECRET_KEY: str = "cmep-dev-change-me-to-at-least-32-chars-long-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    jwt: JWTSettings | None = None
    redis: RedisSettings = Field(default_factory=RedisSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:3001/api/auth/callback/google"

    NEXT_PUBLIC_API_URL: str = "http://127.0.0.1:8001"
    NEXT_PUBLIC_GOOGLE_CLIENT_ID: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if v is None or v == "":
            return ["http://127.0.0.1:3001", "http://localhost:3001"]
        if isinstance(v, list):
            return v
        s = str(v).strip()
        if s.startswith("["):
            import json
            return json.loads(s)
        return [p.strip() for p in s.split(",") if p.strip()]

    def model_post_init(self, __context) -> None:
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


settings = Settings()

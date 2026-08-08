"""
CMEP Platform — Core Configuration
==================================
Pydantic Settings pre nacitanie .env premennych.
Vsetky hodnoty su validovane pri starte aplikacie.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
import os
import secrets as secrets_mod
import string
import warnings


class DatabaseSettings(BaseSettings):
    """PostgreSQL konfiguracia."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    db: str = Field(default="recyclehub", alias="POSTGRES_DB")
    user: str = Field(default="recyclehub", alias="POSTGRES_USER")
    password: str = Field(default="", alias="POSTGRES_PASSWORD")

    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @property
    def sync_url(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RedisSettings(BaseSettings):
    """Redis konfiguracia."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    @property
    def broker_url(self) -> str:
        return f"redis://{self.host}:{self.port}/1"

    @property
    def backend_url(self) -> str:
        return f"redis://{self.host}:{self.port}/2"


class JWTSettings(BaseSettings):
    """JWT autentifikacna konfiguracia."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    secret_key: str = Field(default="", alias="JWT_SECRET_KEY")
    refresh_secret_key: str = Field(default="", alias="JWT_REFRESH_SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    def _generate_dev_secret(self) -> str:
        """Generuje bezpecny dev secret."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_+="
        return "".join(secrets_mod.choice(alphabet) for _ in range(64))

    def model_post_init(self, __context) -> None:
        """Post-init: validacia a auto-generovanie dev secretov."""
        app_env = os.getenv("APP_ENV", "development").lower()

        # Secret key
        if not self.secret_key or len(self.secret_key) < 32:
            if app_env == "production":
                raise ValueError(
                    "JWT_SECRET_KEY musi mat minimalne 32 znakov v produkcii! "
                    "Vygeneruj ho: python3 -c 'import secrets; print(secrets.token_urlsafe(64))'"
                )
            else:
                self.secret_key = self._generate_dev_secret()
                warnings.warn(
                    f"JWT_SECRET_KEY bol auto-generovany pre DEV: {self.secret_key[:8]}... "
                    "Pre produkciu nastav silny JWT_SECRET_KEY v .env!",
                    RuntimeWarning,
                    stacklevel=2,
                )

        # Refresh secret key
        if not self.refresh_secret_key or len(self.refresh_secret_key) < 32:
            if app_env == "production":
                raise ValueError("JWT_REFRESH_SECRET_KEY musi mat minimalne 32 znakov v produkcii!")
            else:
                self.refresh_secret_key = self._generate_dev_secret()
                warnings.warn(
                    f"JWT_REFRESH_SECRET_KEY bol auto-generovany pre DEV.",
                    RuntimeWarning,
                    stacklevel=2,
                )


class CORSSettings(BaseSettings):
    """CORS konfiguracia."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    allowed_origins: List[str] = Field(default=["http://localhost:3000"], alias="CORS_ALLOWED_ORIGINS")
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], alias="ALLOWED_HOSTS")


class MinIOSettings(BaseSettings):
    """MinIO / S3 konfiguracia."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    root_user: str = Field(default="minioadmin", alias="MINIO_ROOT_USER")
    root_password: str = Field(default="", alias="MINIO_ROOT_PASSWORD")
    endpoint: str = Field(default="http://localhost:9000", alias="MINIO_ENDPOINT")
    secure: bool = Field(default=False, alias="MINIO_SECURE")
    bucket_name: str = Field(default="recyclehub-documents", alias="S3_BUCKET_NAME")
    endpoint_url: str = Field(default="http://localhost:9000", alias="S3_ENDPOINT_URL")


class EmailSettings(BaseSettings):
    """SMTP email konfiguracia."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    smtp_host: str = Field(default="localhost", alias="EMAIL_SMTP_HOST")
    smtp_port: int = Field(default=587, alias="EMAIL_SMTP_PORT")
    smtp_user: str = Field(default="", alias="EMAIL_SMTP_USER")
    smtp_password: str = Field(default="", alias="EMAIL_SMTP_PASSWORD")
    from_address: str = Field(default="noreply@recyclehub.local", alias="EMAIL_FROM")
    use_tls: bool = Field(default=True, alias="EMAIL_TLS")


class RateLimitSettings(BaseSettings):
    """Rate limiting konfiguracia."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    period: int = Field(default=60, alias="RATE_LIMIT_PERIOD")


class Settings(BaseSettings):
    """
    Hlavna aplikacna konfiguracia.
    Nacitava hodnoty z .env suboru v koreni projektu.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="RecycleHub Platform", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # --- Sub-settings ---
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    minio: MinIOSettings = Field(default_factory=MinIOSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)

    # --- Monitoring ---
    prometheus_multiproc_dir: str = Field(default="/tmp/prometheus_multiproc", alias="PROMETHEUS_MULTIPROC_DIR")

    # --- GDPR ---
    gdpr_enabled: bool = Field(default=True, alias="GDPR_ENABLED")
    gdpr_cookie_consent: bool = Field(default=True, alias="GDPR_COOKIE_CONSENT")

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


# Singleton instance
settings = Settings()

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    app_name: str = "geo3-ip-webserver"
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60
    geoip_db_path: str = "./GeoLite2-City.mmdb"
    geoip_cache_ttl_seconds: int = Field(default=3600, ge=1)
    artifact_bucket: str = "artifacts"
    artifact_endpoint_url: str | None = None
    artifact_region: str | None = None
    artifact_access_key: str | None = None
    artifact_secret_key: str | None = None
    artifact_use_ssl: bool = True
    database_url: str = "postgresql+psycopg://geo3:geo3@localhost:5432/geo3"

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("jwt_algorithm must be HS256")
        return value


try:
    settings = Settings()
except ValidationError as exc:
    raise RuntimeError("Invalid application settings") from exc


"""
This file handles application configuration settings.

It provides access to application settings such as database configuration,
JWT settings, CORS origins, and seed manager credentials.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

# Each field is automatically read from the environment variable with the same name
class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_db_name: str = "syncup"

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cors_origins: str = "http://localhost:5173"

    seed_manager_email: str = "admin@syncup.local"
    seed_manager_password: str = "change-me"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

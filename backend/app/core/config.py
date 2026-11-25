from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./dev.db"
    jwt_secret: str = "dev-secret-degistir"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

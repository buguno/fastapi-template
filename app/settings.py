from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    ENVIRONMENT: str = 'development'
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == 'production'


settings = Settings()  # type: ignore

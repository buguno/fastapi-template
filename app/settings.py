from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    ENVIRONMENT: str = 'development'

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == 'production'

    DATABASE_URL: str = Field(init=False)


settings = Settings()

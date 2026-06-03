from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://quant:quant123@localhost:5432/quant_dashboard"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    data_source: str = "akshare"

    class Config:
        env_file = ".env"

settings = Settings()

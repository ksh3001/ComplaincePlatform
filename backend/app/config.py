from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://provenix:provenix@localhost:5432/provenix"
    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "fake"
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = ""
    azure_openai_chat_deployment: str = ""
    azure_openai_embedding_deployment: str = ""
    run_token_budget: int = 400000
    github_token: str = ""


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """環境變數設定。容器內由 docker-compose 注入；本機直接執行時用預設值。"""

    database_url: str = (
        "postgresql+psycopg://english:change-me@localhost:5432/english_practice"
    )
    api_key: str = "dev-local-key"
    default_user_name: str = "default"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

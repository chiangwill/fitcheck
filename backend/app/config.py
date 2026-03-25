from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    gemini_api_key: str
    supabase_url: str = ""
    supabase_key: str = ""

    model_config = {"env_file": "../.env", "extra": "ignore"}


settings = Settings()

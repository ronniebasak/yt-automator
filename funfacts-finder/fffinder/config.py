from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    CHUNKS_DIRECTORY: str = "fact-chunks"
    OPENROUTER_API_KEY: str = ""
    MAX_DIGITS_CHUNK: int = 3
    CHUNK_PREFIX: str = "chunk_"


settings = Settings()
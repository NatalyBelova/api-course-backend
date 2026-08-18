import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/api_course",
    )
    DOCS_USERNAME: str = os.getenv("DOCS_USERNAME", "")
    DOCS_PASSWORD: str = os.getenv("DOCS_PASSWORD", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")


settings = Settings()


from pathlib import Path
from pydantic import HttpUrl, Field
from pydantic_settings import BaseSettings

ENV_PATH = Path(__file__).resolve().parent / ".env.local"


class Settings(BaseSettings):
    resume_pipeline_secret: str = Field(..., alias="RESUME_PIPELINE_HMAC_SECRET")
    next_webhook_url: HttpUrl = Field(..., alias="RESUME_PIPELINE_WEBHOOK_URL")

    model_config = {
        "env_file": ENV_PATH,
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


settings = Settings()  # type: ignore[arg-type]

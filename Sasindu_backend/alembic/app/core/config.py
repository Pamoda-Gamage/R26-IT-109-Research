from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# pydantic-settings' env_file only populates the Settings model below -- it does not
# put .env values into os.environ for other libraries (e.g. the Anthropic SDK, which
# reads ANTHROPIC_API_KEY straight from the process environment). Loading it globally
# here, once, before anything else in the app imports, covers both.
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    seed: int = 42
    environment: Literal["dev", "test", "prod"] = "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()

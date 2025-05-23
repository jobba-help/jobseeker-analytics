import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode
from fastapi import BackgroundTasks
from typing import List, Any
from typing_extensions import Annotated
import logging
from browserbase import Browserbase

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    GOOGLE_SCOPES: Annotated[List[str], NoDecode]
    REDIRECT_URI: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_API_KEY: str
    COOKIE_SECRET: str
    CLIENT_SECRETS_FILE: str = "credentials.json"
    ENV: str = "dev"
    APP_URL: str
    ORIGIN: str = ".jobba.help"
    DATABASE_URL: str = "default-for-local"
    DATABASE_URL_LOCAL_VIRTUAL_ENV: str = (
        "postgresql://postgres:postgres@localhost:5433/jobseeker_analytics"
    )
    DATABASE_URL_DOCKER: str = (
        "postgresql://postgres:postgres@db:5432/jobseeker_analytics"
    )
    BROWSERBASE_API_KEY: str = "default-for-local"
    BROWSERBASE_PROJECT_ID: str = "default-for-local"
    OPENAI_API_KEY: str = "default-for-local"
    GOOGLE_CSE_API_KEY: str = "default-for-local"
    GOOGLE_CSE_ID: str = "default-for-local"  # https://programmablesearchengine.google.com/controlpanel/
    OPENAI_MODEL: str = "gpt-4.1-nano"
    # background tasks instance of fastapi background tasks
    background_tasks: BackgroundTasks = BackgroundTasks()
    bb_client: Any = None
    bb_session: Any = None

    @field_validator("GOOGLE_SCOPES", mode="before")
    @classmethod
    def decode_scopes(cls, v: str) -> List[str]:
        logger.info("Decoded scopes from string: %s", json.loads(v.strip("'\"")))
        return json.loads(v.strip("'\""))

    @property
    def is_publicly_deployed(self) -> bool:
        return self.ENV in ["prod", "staging"]

    def get_browserbase_session(self) -> Any:
        """Get or create a Browserbase session."""
        if self.bb_client is None:
            self.bb_client = Browserbase(api_key=self.BROWSERBASE_API_KEY)
        
        if self.bb_session is None:
            self.bb_session = self.bb_client.sessions.create(project_id=self.BROWSERBASE_PROJECT_ID)
            logger.info(f"Created new Browserbase session: {self.bb_session.id}")
        
        return self.bb_session

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings(_env_file=".env", _env_file_encoding="utf-8")

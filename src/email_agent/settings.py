from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os

class Settings(BaseSettings):
    gmail_client_secret_file: str = Field(default=os.getenv("GMAIL_CLIENT_SECRET_FILE", "secrets/oauth_client.json"))
    gmail_token_file: str = Field(default=os.getenv("GMAIL_TOKEN_FILE", "secrets/token.json"))
    gmail_scopes: List[str] = Field(
    default_factory=lambda: [
        s.strip().strip('"').strip("'")
        for s in os.getenv(
            "GMAIL_SCOPES", "https://www.googleapis.com/auth/gmail.modify"
        ).split(",") if s.strip()
    ]
)
    default_labels: List[str] = Field(default_factory=lambda: [s.strip() for s in os.getenv(
        "DEFAULT_LABELS", 
        "Newsletters,Receipts,Travel,Personal,Work,Finance,Promotions,Notifications,Family,Urgent"
    ).split(",") if s.strip()])
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    

    class Config:
        env_prefix = ""
        env_file = ".env"
        extra = "ignore"

settings = Settings()
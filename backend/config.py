import os
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict

# macOS Python doesn't use system CA certs — patch with certifi if available
if sys.platform == "darwin" and not os.environ.get("SSL_CERT_FILE"):
    try:
        import certifi

        os.environ["SSL_CERT_FILE"] = certifi.where()
    except ImportError:
        pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    neo4j_uri: str = "neo4j+s://9e09bf68.databases.neo4j.io"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"

    cors_origins: str = "http://localhost:3000"

    # rate limiting
    graph_rate_limit: int = 100  # per minute
    chat_rate_limit: int = 10  # per minute


settings = Settings()

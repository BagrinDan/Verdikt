
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    codeql_workspace_dir: Path = Path("/var/shared/workspace")
    codeql_results_dir: Path = Path("/var/shared/results")
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  
    )

settings = Settings()

settings.codeql_workspace_dir.mkdir(parents=True, exist_ok=True)
settings.codeql_results_dir.mkdir(parents=True, exist_ok=True)
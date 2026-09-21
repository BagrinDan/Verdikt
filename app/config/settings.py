
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    codeql_workspace_dir: Path
    codeql_results_dir: Path
    
    codeql_execution_mode: str = "local"
    codeql_container_name: str = "verdikt-codeql"
    debug: bool = True
    docker_gid: int = 961

    class Config:
        env_file = ".env"

settings = Settings()
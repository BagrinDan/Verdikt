
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    codeql_workspace_dir: Path
    codeql_results_dir: Path
    
    codeql_execution_mode: str 
    codeql_container_name: str = "verdikt-codeql"
    debug: bool = True
    docker_gid: int = 961

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
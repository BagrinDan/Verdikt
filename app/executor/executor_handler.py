from app.config.settings import settings
from .local_executor import LocalCodeQlExecutor
from .docker_executor import DockerCodeQlExecutor
from .executor import CodeQlExecutor
from loguru import logger



def get_codeql_executor() -> CodeQlExecutor:
    logger.info(f"DEBUG: settings.codeql_execution_mode = >{settings.codeql_execution_mode}<")

    if settings.codeql_execution_mode == "docker":
        return DockerCodeQlExecutor(
            container_name=settings.codeql_container_name,
            workspace_dir=settings.codeql_workspace_dir,
            results_dir=settings.codeql_results_dir
        )
    return LocalCodeQlExecutor()
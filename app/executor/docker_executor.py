import asyncio
from pathlib import Path
from loguru import logger
from .executor import CodeQlExecutor


class DockerCodeQlExecutor(CodeQlExecutor):
    """Вызывает codeql внутри отдельного контейнера через docker exec.
    Сам разруливает перевод host-путей в пути внутри codeql-контейнера —
    вызывающий код об этом вообще не знает."""

    def __init__(self, container_name: str, workspace_dir: Path, results_dir: Path,
                 container_workspace: str = "/workspace", container_results: str = "/results"):
        self.container_name = container_name
        self.workspace_dir = workspace_dir
        self.results_dir = results_dir
        self.container_workspace = container_workspace
        self.container_results = container_results

    def _to_container_path(self, host_path: Path) -> str:
        try:
            relative = host_path.relative_to(self.workspace_dir)
            return f"{self.container_workspace}/{relative}"
        except ValueError:
            pass
        try:
            relative = host_path.relative_to(self.results_dir)
            return f"{self.container_results}/{relative}"
        except ValueError:
            raise ValueError(f"[EXCEPTION | DockerCodeQlExecutor] Path {host_path} is not under a shared volume")

    async def create_database(self, db_dir: Path, source_dir: Path, language: str) -> None:
        cmd = [
            "docker", "exec", self.container_name,
            "codeql", "database", "create",
            self._to_container_path(db_dir),
            f"--language={language}",
            f"--source-root={self._to_container_path(source_dir)}",
            "--overwrite"
        ]
        await self._run(cmd, "db init")

    async def analyze(self, db_dir: Path, sarif_file: Path, language: str) -> None:
        cmd = [
            "docker", "exec", self.container_name,
            "codeql", "database", "analyze",
            self._to_container_path(db_dir),
            f"{language}-code-scanning.qls",
            "--format=sarif-latest",
            f"--output={self._to_container_path(sarif_file)}"
        ]
        await self._run(cmd, "analyze")

    async def _run(self, cmd: list[str], label: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        logger.debug(f"[DEBUG | DockerCodeQlExecutor]: CodeQL CLI ({label}) response: "
                     f"output {stdout.decode()}. errors {stderr.decode()}")
        if proc.returncode != 0:
            raise RuntimeError(f"[EXCEPTION | DockerCodeQlExecutor] CodeQL {label} failed: {stderr.decode()}")
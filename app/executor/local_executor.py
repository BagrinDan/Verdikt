import asyncio
from pathlib import Path
from loguru import logger
from .executor import CodeQlExecutor


class LocalCodeQlExecutor(CodeQlExecutor):

    async def create_database(self,
                              db_dir: Path,
                              source_dir: Path, 
                              language: str ) -> None:
        cmd = [
            "codeql", "database", "create",
            str(db_dir),
            f"--language={language}",
            f"--source-root={source_dir}",
            "--overwrite"
        ]
        await self._run(cmd, "db init")
    
    async def analyze(self, db_dir: Path, sarif_file: Path, language: str) -> None:
        cmd = [
            "codeql", "database", "analyze",
            str(db_dir),
            f"{language}-code-scanning.qls",
            "--format=sarif-latest",
            f"--output={sarif_file}"
        ]
        await self._run(cmd, "analyze")

    async def _run(self, cmd: list[str], label: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        logger.debug(f"[DEBUG | LocalCodeQlExecutor]: CodeQL CLI ({label}) response: "
                     f"output {stdout.decode()}. errors {stderr.decode()}")
        if proc.returncode != 0:
            raise RuntimeError(f"[EXCEPTION | LocalCodeQlExecutor] CodeQL {label} failed: {stderr.decode()}")
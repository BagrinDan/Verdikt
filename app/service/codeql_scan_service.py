import asyncio
from pathlib import Path
from app.config.settings import settings
from app.service.interface.code_scan_interface import CodeQlScanInterface
from app.models.scan_request import ScanRequest
import uuid
from loguru import logger



class CodeQlScanService(CodeQlScanInterface):
    def __init__(self):
        self.workspace_dir: Path = settings.codeql_workspace_dir
        self.results_dir: Path = settings.codeql_results_dir

    async def clone_repo(self, payload: ScanRequest) -> Path:
        source_dir = self.workspace_dir / payload.scan_id
        source_dir.mkdir(parents=True, exist_ok=True)

        clone_cmd = ["git", "clone", "--depth", "1"]
        if payload.branch:
            clone_cmd += ["--branch", payload.branch, "--single-branch"]
        clone_cmd += [payload.repo_url, str(source_dir)]

        proc = await asyncio.create_subprocess_exec(
            *clone_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Git clone failed: {stderr.decode()}")
        return source_dir


    async def run_full_scan(self, payload: ScanRequest) -> Path:
        if not payload.scan_id:
            payload.scan_id = str(uuid.uuid4())
        logger.info(f"Generated scan_id={payload.scan_id} for repo={payload.repo_url}")
        await self.clone_repo(payload)
        return await self.run_codeql_scan(payload)
    

    async def run_codeql_scan(self, payload: ScanRequest):
        source_dir = self.workspace_dir / payload.scan_id
        db_dir = self.results_dir / f"db_{payload.scan_id}"
        sarif_file = self.results_dir / f"results_{payload.scan_id}.sarif"

        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        create_db_cmd = [
            "codeql", "database", "create",
            str(db_dir),
            f"--language={payload.language}",
            f"--source-root={source_dir}",
            "--overwrite"
        ]

        proc = await asyncio.create_subprocess_exec(
            *create_db_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"CodeQL DB creation failed: {stderr.decode()}")

        analyze_cmd = [
            "codeql", "database", "analyze",
            str(db_dir),
            f"{payload.language}-code-scanning.qls",  
            "--format=sarif-latest",
            f"--output={sarif_file}"
        ]

        proc = await asyncio.create_subprocess_exec(
            *analyze_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"CodeQL analysis failed: {stderr.decode()}")

        return sarif_file
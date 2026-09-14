import asyncio
from pathlib import Path
from app.config.settings import settings
from app.service.interface.code_scan_interface import CodeQlScanInterface
from app.models.scan_request import ScanRequest
import uuid
from loguru import logger


# Класс который отвечает за работу сканирования используя Codeql

# TODO: 1

class CodeQlScanService(CodeQlScanInterface):
    def __init__(self):
        self.workspace_dir: Path = settings.codeql_workspace_dir
        self.results_dir: Path = settings.codeql_results_dir

    # ----------------------------
    # Собираем payload и выполняет 
    # -----------------------------
    async def run_full_scan(self, payload: ScanRequest) -> Path:
        payload.scan_id = str(uuid.uuid4())

        logger.info(f"[INFO | CodeQlScanService] Generated scan_id={payload.scan_id} \
                    for repo={payload.repo_url} \
                    on branch={payload.branch} \
                    language={payload.language}" )

        source_dir = await self.clone_repo(payload)
        sarif_file = await self.run_codeql_scan(payload, source_dir) 

        return sarif_file
    # TODO: Добавить тут вызов ML и LLM с последующей очисткой папков


    # ----------------------------------------------------------------
    # Данный метод клонирует репозитории локально в codeql/workspace 
    # для дальнейшей сохранения результат в codeql/results
    # ----------------------------------------------------------------
    async def clone_repo(self, payload: ScanRequest) -> Path:
        # Создаем папки где будет проделан анализ
        source_dir = self.workspace_dir / payload.scan_id
        result_dir = self.results_dir

        # Создаем их если их нет
        source_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)

        # Формируем гит команду которая сделает клонированиет  
        clone_cmd = [
                    "git", 
                    "clone", 
                    "--depth", "1", # Скачиваем последний коммит, чтобы не загрузать лишнего 
                    "--branch", 
                    payload.branch, 
                    payload.repo_url, 
                    str(source_dir)
        ]

        # Создает асинхронное скачивание ветки 
        proc = await asyncio.create_subprocess_exec(
            *clone_cmd, # Распаковка полученной ветки
            stdout=asyncio.subprocess.PIPE, # Перехватываем поток выводов Гита
            stderr=asyncio.subprocess.PIPE # Перехватываем поток ошибок гита
        )

        _, stderr = await proc.communicate()
        logger.debug(f"[DEBUG | CodeQlScanService]: Github response: Output {stderr.decode()}") 

        if proc.returncode != 0:
            raise RuntimeError(f"[EXCEPTION | CodeQlScanService] Git clone failed: {stderr.decode()}")
        
        return source_dir    


    # ------------------------------------------------
    # Данный метод выполняет сканирования через Codeql
    # ------------------------------------------------
    async def run_codeql_scan(self, payload: ScanRequest, source_dir: Path):
        # Директории workspace & results, а так же .sarif
        db_dir = self.results_dir / f"db_{payload.scan_id}"
        sarif_file = self.results_dir / f"results_{payload.scan_id}.sarif"

        # Создает команду для CodeQL CLI 
        create_db_cmd = [
            "codeql", "database", "create",
            str(db_dir),
            f"--language={payload.language}",
            f"--source-root={source_dir}",
            "--overwrite"
        ]

        # Создает ассин.процесс для создаение базы данных
        proc = await asyncio.create_subprocess_exec(
            *create_db_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        logger.debug(f"[DEBUG | CodeQlScanService]: CodeQL CLI (db init) response: \
                     \noutput {stdout.decode()}. \
                     \nErrors {stderr.decode()}")

        if proc.returncode != 0:
            raise RuntimeError(f"[EXCEPTION | CodeQlScanService] CodeQL DB creation failed: {stderr.decode()}")

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
        logger.debug(f"[DEBUG | CodeQlScanService]: CodeQL CLI (scan) response: \
                     \noutput {stdout.decode()}. \
                     \nErrors {stderr.decode()}")

        if proc.returncode != 0:
            raise RuntimeError(f"CodeQL analysis failed: {stderr.decode()}")

        return sarif_file
    


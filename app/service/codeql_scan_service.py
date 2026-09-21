import asyncio
from pathlib import Path
from app.config.settings import settings
from app.service.interface.code_scan_interface import CodeQlScanInterface
from app.models.scan_request import ScanRequest
from app.executor.executor_handler import get_codeql_executor
import uuid
from loguru import logger
from app.helper.git_branch_check import check_remote_branch_exists


# Класс который отвечает за работу сканирования используя Codeql

# TODO: 1

class CodeQlScanService(CodeQlScanInterface):
    def __init__(self):
        self.workspace_dir: Path = settings.codeql_workspace_dir
        self.results_dir: Path = settings.codeql_results_dir
        self.executor = get_codeql_executor()

    # ---------------------------------------
    # Читает payload и выполняет сканирование 
    # ---------------------------------------
    async def run_full_scan(self, payload: ScanRequest) -> Path:
        payload.scan_id = str(uuid.uuid4())

        logger.info(
            f"Generated scan_id={payload.scan_id}"
            f"for repo={payload.repo_url}" 
            f"on branch={payload.branch}"
            f"language={payload.language}" 
        )

        source_dir = await self.clone_repo(payload)
        db_dir, sarif_file = await self.create_codeql_db(payload, source_dir) 
        sarif_file = await self.run_codeql_analyz(db_dir, payload, sarif_file)

        return sarif_file
    # TODO: Добавить тут вызов ML и LLM с последующей очисткой папков


    # ----------------------------------------------------------------
    # Данный метод клонирует репозитории локально в codeql/workspace 
    # для дальнейшей сохранения результат в codeql/results
    # ----------------------------------------------------------------
    async def clone_repo(self, payload: ScanRequest) -> Path:
        # Проверяем если бранч валидный
        await check_remote_branch_exists(payload.repo_url, payload.branch)

        # Создаем папки где будет проделан анализ
        source_dir = self.workspace_dir / payload.scan_id
        result_dir = self.results_dir

        # Создаем их если их нет
        source_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)

        # Проверяем executor
        logger.info(f"[INFO | CodeQlScanService] Executor {self.executor.__class__.__name__}")

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


    # ------------------------------------------------------
    # Данный метод выполняет создает внутрению бд для Codeql
    # ------------------------------------------------------
    async def create_codeql_db(self, payload: ScanRequest, source_dir: Path):
        db_dir = self.results_dir / f"db_{payload.scan_id}"
        sarif_file = self.results_dir / f"results_{payload.scan_id}.sarif"
        
        await self.executor.create_database(db_dir, source_dir, payload.language)

        return db_dir, sarif_file
    
    # -----------------------------------------------
    # Инициализация сканирования склонированного репо
    # -----------------------------------------------
    async def run_codeql_analyz(self, db_dir: Path, payload: ScanRequest, sarif_file):
        await self.executor.analyze(db_dir, sarif_file, payload.language)
        return sarif_file 


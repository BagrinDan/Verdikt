import asyncio
from pathlib import Path
import uuid
from loguru import logger

from app.config.settings import settings
from app.service.interface.code_scan_interface import CodeQlScanInterface
from app.models.requests.scan_request import ScanRequest
from app.executor.executor_handler import get_codeql_executor
from app.helper.git_branch_check import check_remote_branch_exists
from app.core.exceptions.git_branch_exception import GitBranchNotFoundError

#
# Класс который отвечает за работу сканирования используя Codeql
#
# Что делает класс: 
# 1. сделать клон репозитория (отвечает метод clone_repo()), 
# 2. инициализировать базу данных codeql (отвечает метод create_codeql_db())
# 3. выполнить сканирование (отвечает метод run_codeql_analyz())


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

    # ----------------------------------------------------------------
    # Данный метод клонирует репозитории локально в codeql/workspace 
    # для дальнейшей сохранения результат в codeql/results
    # ----------------------------------------------------------------
    async def clone_repo(self, payload: ScanRequest) -> Path:
        branch_check = await check_remote_branch_exists(payload.repo_url, payload.branch)

        logger.info(f"[INFO | CodeQlScanService] Branch check: {branch_check}")
        if branch_check is not None:     # функция возвращает Null если бранч существует
            raise GitBranchNotFoundError(
                repo_url=payload.repo_url,
                branch=payload.branch,
                message=branch_check.get("message")
            )

        # Инициализируем папки для CodeQL
        source_dir = self.workspace_dir / payload.scan_id
        result_dir = self.results_dir

        # Создаем их если их нет (просто при очистке мы просто будем сносить директории)
        source_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)

        # Проверяем executor (либо докер либо локалка)
        # Это нужно чтобы понять если была выбрана правильная среда запуска кода
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
            *clone_cmd, 
            stdout=asyncio.subprocess.PIPE, # Сохраняем поток выводов Гита 
            stderr=asyncio.subprocess.PIPE # Сохраняем поток ошибок гита
            # stdout бесполезен т.к гит используем stdout что для ошибок что для логов
            # но данная функция требует его, иначе будет ошибка
        )

        _, stderr = await proc.communicate() # Пропускаем stdout, т.к гит использует только stderr для логов
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


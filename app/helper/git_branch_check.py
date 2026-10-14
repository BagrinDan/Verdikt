import asyncio
from typing import Dict, Any
from loguru import logger
import os



async def check_remote_branch_exists(repo_url: str, branch: str) -> Dict[str, Any]:
    """
    Проверяет существование ветки в удаленном репозитории.
    Возвращает словарь со статусом и информацией.
    """

    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"      # Запрещает текстовый ввод пароля в терминал
    env["GIT_ASKPASS"] = ""               # Отключает внешние программы запроса пароля (включая окна VS Code)
    env["GIT_CREDENTIAL_HELPER"] = ""     # Отключает системные креденшалы

    check_branch_cmd = ["git", "ls-remote", "--heads", repo_url, branch]

    proc_check = await asyncio.create_subprocess_exec(
        *check_branch_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    stdout, stderr = await proc_check.communicate()

    output_str = stdout.decode("utf-8").strip()
    error_str = stderr.decode("utf-8").strip()

    logger.info(f"[INFO | GitBrancCheck] Stdout : {output_str}, Stderr: {error_str}")

    if proc_check.returncode != 0 or not output_str:
        return False

    return True

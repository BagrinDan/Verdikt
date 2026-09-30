import asyncio
from typing import Dict, Any
from loguru import logger


async def check_remote_branch_exists(repo_url: str, branch: str) -> Dict[str, Any]:
    """
    Проверяет существование ветки в удаленном репозитории.
    Возвращает словарь со статусом и информацией.
    """
    try:
        check_branch_cmd = ["git", "ls-remote", "--heads", repo_url, branch]

        proc_check = await asyncio.create_subprocess_exec(
            *check_branch_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc_check.communicate()

        logger.info(f"[INFO | GitBrancCheck] Stdout : {stdout}, Stderr: {stderr}")

        # Если вывод пустой — ветка не найдена
        if not stdout.strip():
            if branch == 'main':
                tip = " Tip: Maybe it is not MAIN, but MASTER?" if branch == "main" else ""
                return {
                    "success": False,
                    "exists": False,
                    "message": f"Branch '{branch}' does not exist in this repository.\n{tip}"
                }
            else:
                return {
                    "success": False,
                    "exists": False,
                    "message": f"Branch '{branch}' does not exist in this repository."
                }

    except Exception as e:
        return {
            "success": False,
            "exists": False,
            "message": f"Unexpected error while checking branch: {str(e)}"
        }
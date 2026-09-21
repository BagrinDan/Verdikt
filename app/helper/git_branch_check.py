

import asyncio

async def check_remote_branch_exists(repo_url: str, branch: str) -> None:
    """
    Проверяет существование ветки в удаленном репозитории.
    Выбрасывает ValueError, если ветка не найдена.
    """
    check_branch_cmd = ["git", "ls-remote", "--heads", repo_url, branch]

    proc_check = await asyncio.create_subprocess_exec(
        *check_branch_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc_check.communicate()

    if not stdout.strip():
        if branch == 'main':
            raise ValueError(
                f"[EXCEPTION | GitUtils] Branch 'main' does not exist in repository {repo_url}. "
                "💡 Tip: Maybe it is not MAIN, but MASTER?"
            )
        raise ValueError(f"[EXCEPTION | GitUtils] Branch '{branch}' does not exist in repository {repo_url}")
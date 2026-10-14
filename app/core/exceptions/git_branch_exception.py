from app.core.exceptions.base import AppException

class GitBranchNotFoundError(AppException):
    status_code = 404
    error_code = "GIT_BRANCH_NOT_FOUND"
    default_message = "This branch doesn't exist in this repo."

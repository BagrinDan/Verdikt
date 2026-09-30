from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from app.core.exceptions.base import AppException

app = FastAPI()

@app.exception_handler(AppException)
async def git_branch_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message
        }
    )
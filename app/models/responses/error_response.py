from pydantic import BaseModel
from typing import Optional

class ErrorResponseDTO(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: Optional[dict] = None
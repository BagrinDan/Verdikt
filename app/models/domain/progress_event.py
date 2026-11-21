from typing import Literal, Optional
from pydantic import BaseModel


class ProgressEvent(BaseModel):
    step: Literal["codeql", "llm", "verdict"]
    status: Literal["active", "completed", "error"]
    message: str = ""
    current: Optional[int] = None
    total: Optional[int] = None

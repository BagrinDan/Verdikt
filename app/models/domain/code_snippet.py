from pydantic import BaseModel, Field
from typing import Optional


class CodeSnippet(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    start_column: Optional[int] = None
    end_column: Optional[int] = None
    code: str = ""
    message: str = ""
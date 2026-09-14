from pydantic import BaseModel, field_validator
from typing import Optional

class ScanRequest(BaseModel):
    scan_id: Optional[str] = None
    repo_url: str  
    branch: Optional[str] = "main" 
    language: str

    @field_validator("repo_url")
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        if not v.startswith("https://github.com/") and not v.startswith("https://gitlab.com/"):
            raise ValueError("Only https GitHub/GitLab URLs are allowed")
        return v
    
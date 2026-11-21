from pathlib import Path
from pydantic import BaseModel


class CodeQlScanResult(BaseModel):
    scan_id: str
    sarif_path: Path
    source_dir: Path
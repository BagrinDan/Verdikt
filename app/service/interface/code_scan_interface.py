from abc import ABC, abstractmethod
from pathlib import Path
from app.models.scan_request import ScanRequest


class CodeQlScanInterface(ABC):
    @abstractmethod
    async def run_full_scan(self, payload: ScanRequest) -> Path | dict:
        pass
from abc import ABC, abstractmethod
from pathlib import Path


class CodeQlExecutor(ABC):
    
    @abstractmethod
    async def create_database(self,
                              db_dir: Path,
                              source_dir: Path, 
                              language: str ) -> None:
        ...

    @abstractmethod
    async def analyze(self, 
                      db_dir: Path,
                      sarif_file: Path, 
                      language: str ) -> None:
        ...
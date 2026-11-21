import asyncio
from typing import AsyncIterator

from loguru import logger

from app.models.domain.progress_event import ProgressEvent
from app.models.requests.scan_request import ScanRequest
from app.pipeline.sarif_parser import SarifParser
from app.service.interface.code_scan_interface import CodeQlScanInterface


# TODO: ENUM ащк step and status


class ScanOrchestrator:
    def __init__(self, codeql: CodeQlScanInterface):
        self.codeql = codeql

    async def run(self, payload: ScanRequest) -> AsyncIterator[ProgressEvent]:
        step = "codeql"
        try:
            # 1. CodeQL
            yield ProgressEvent(step="codeql", 
                                status="active", 
                                message="Cloning repo and analyze")
            
            scan = await self.codeql.run_full_scan(payload)                 # CodeQlScanResult
            
            yield ProgressEvent(step="codeql", 
                                status="completed", 
                                message=f"SARIF: {scan.sarif_path.name}")

            # 2. Building TaintPath
            yield ProgressEvent(step="codeql", 
                                status="active", 
                                message="Resolving SARIF")

            parser = SarifParser(source_dir=scan.source_dir, 
                                 context_lines=5,  # Could be setted by AI
                                 max_flows_per_result=5)
            
            paths = await asyncio.to_thread(parser.parse, scan.sarif_path)   # список TaintPath
            
            yield ProgressEvent(step="codeql",
                                status="active",
                                message=f"Total of paths: {len(paths)}")

            # 3. Дальше: детектор, RAG, советы, отчёт (paths уже доступен)
            step = "salieri"

            yield ProgressEvent(step="salieri",
                                status="active",
                                message=f"Total of paths: {len(paths)}")

            
            yield ProgressEvent(step="salieri",
                                status="active",
                                message=f"Total of paths: {len(paths)}")



        except Exception as e:
            logger.exception("[ERROR | orchestrator] scan failed at step={}", step)
            yield ProgressEvent(step=step, status="error", message=str(e))

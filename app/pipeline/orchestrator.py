import asyncio
from typing import AsyncIterator
from loguru import logger

from app.models.domain.progress_event import ProgressEvent
from app.models.requests.scan_request import ScanRequest
from app.pipeline.sarif_parser import SarifParser
from app.service.interface.code_scan_interface import CodeQlScanInterface
from app.models.domain.enums import Step
from app.models.responses.codeql_scan_result import CodeQlScanResult
from app.models.domain.taint_path import TaintPath


# Параметры алертов. Чем выше значения тем больше подробностей
INITIAL_CONTEXT_LINES = 5      
MAX_FLOWS_PER_RESULT = 5

# Оркестратор который собирает все этапы в месте в целью выполнить работу
# и вернуть поэтапную информацию 

class ScanOrchestrator:
    def __init__(self, codeql: CodeQlScanInterface):
        self.codeql = codeql

    async def run(self, payload: ScanRequest) -> AsyncIterator[ProgressEvent]:
        step = Step.CODEQL
        try:
            # 1. CodeQL
            yield ProgressEvent.active(step, "Cloning repo and analyzing")
            scan = await self.codeql.run_full_scan(payload)
            yield ProgressEvent.completed(step, f"SARIF: {scan.sarif_path.name}")

            # 2. Разбор SARIF в TaintPath
            yield ProgressEvent.active(step, "Resolving SARIF")
            paths = await self._build_taint_paths(scan)
            yield ProgressEvent.completed(step, f"Total of paths: {len(paths)}")

            # 3. Детектор (Salieri)
            # step = Step.SALIERI
            # yield ProgressEvent.active(step, f"Analyzing {len(paths)} paths")
            # verdicts = await self._detect(paths)

            # 4. Отчет (Amadeus)
            

        except Exception as e:
            logger.exception("[ERROR | orchestrator] scan failed at step={}", step)
            yield ProgressEvent.error(step, str(e))


    async def _build_taint_paths(self, scan: CodeQlScanResult) -> list[TaintPath]:
        parser = SarifParser(source_dir=scan.source_dir,
                             context_lines=INITIAL_CONTEXT_LINES,
                             max_flows_per_result=MAX_FLOWS_PER_RESULT)
        return await asyncio.to_thread(parser.parse, scan.sarif_path)

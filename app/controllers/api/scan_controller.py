# Python Libs
import json
from fastapi import APIRouter, Depends
from loguru import logger
from fastapi.responses import StreamingResponse
import asyncio

# Dependency
from app.service.interface.code_scan_interface import CodeQlScanInterface
from app.service.codeql_scan_service import CodeQlScanService
from app.models.requests.scan_request import ScanRequest
from app.pipeline.orchestrator import ScanOrchestrator 


router = APIRouter(prefix="/static_analyze", tags=["analyze_via_codeql"])

# Get dependency
def get_orchestrator() -> ScanOrchestrator:
    return ScanOrchestrator(codeql=CodeQlScanService())


# Main scan method
@router.post("/scaning")
async def start_scan(payload: ScanRequest,
                     orchestrator: ScanOrchestrator = Depends(get_orchestrator)):   
    async def stream():
        async for event in orchestrator.run(payload):
            print("[LOGSS]" + event.model_dump_json() + "\n")
            yield event.model_dump_json() + "\n"
    
    return StreamingResponse(stream(), media_type="application/x-ndjson")
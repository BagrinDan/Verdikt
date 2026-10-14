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


router = APIRouter(prefix="/static_analyze", tags=["analyze_via_codeql"])

def get_scan_service() -> CodeQlScanInterface:
    return CodeQlScanService()

@router.post("/scaning")
async def start_scan(payload: ScanRequest,
                       service: CodeQlScanInterface = Depends(get_scan_service)):   
     
    logger.info(f"[INFO | scan_router->trigger_scan] Got payload {payload.repo_url}, {payload.branch}, {payload.language}")
    
    async def event_generator():
        try:
            yield json.dumps({"step": "codeql", "status": "active"}) + "\n"

            # 1. CodeQL Scanning        
            sarif_path = await service.run_full_scan(payload)
            logger.info(f"[INFO | scan_router->trigger_scan] sarif path : {sarif_path}")

            with open(sarif_path, "r", encoding="utf-8") as f:
                sarif_data = json.load(f)

            yield json.dumps({"step": "codeql", "status": "completed"}) + "\n"
            

            yield json.dumps({"status": "success", "message": "CodeQl finished work..."}) + "\n"   
             
            await asyncio.sleep(2)

            # 2. ML
            # 3. Secondary LLM
            # 4. Main LLM
                
            yield json.dumps({"status": "success", "message": "Scanning complete "}) + "\n"
            
        except Exception as e:
            yield json.dumps({"step": "codeql", "status": "error", "message": str(e)}) + "\n"
        
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
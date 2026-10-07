import json
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

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

    try:
        # 1. CodeQL Scanning        
        sarif_path = await service.run_full_scan(payload)
        
        with open(sarif_path, "r", encoding="utf-8") as f:
            sarif_data = json.load(f)
            
        # 2. ML
        # 3. Secondary LLM
        # 4. Main LLM
            
        return {
            "status": "success",
            "message": "scanning complete"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", 
                    "message": str(e)
            }
        )
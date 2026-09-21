import json
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.service.interface.code_scan_interface import CodeQlScanInterface
from app.service.codeql_scan_service import CodeQlScanService
from app.models.scan_request import ScanRequest


router = APIRouter(prefix="/static_analyze", tags=["analyze_via_codeql"])


def get_scan_service() -> CodeQlScanInterface:
    return CodeQlScanService()


@router.post("/codeql")
async def codeql_scan(payload: ScanRequest,
                       service: CodeQlScanInterface = Depends(get_scan_service)):   
     
    logger.info(f"[INFO | scan_router->trigger_scan] Got payload {payload.repo_url}, {payload.branch}, {payload.language}")

    try:
        sarif_path = await service.run_full_scan(payload)
        
        with open(sarif_path, "r", encoding="utf-8") as f:
            sarif_data = json.load(f)
            
        return {
            "status": "success",
            "scan_id": payload.scan_id,
            "findings_count": len(sarif_data.get("runs", [{}])[0].get("results", [])),
            "report": sarif_data
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": str(e)}
        )
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
from fastapi import FastAPI, HTTPException
from app.service.interface.code_scan_interface import CodeQlScanInterface
from app.service.codeql_scan_service import CodeQlScanService
from app.models.scan_request import ScanRequest
from loguru import logger


#-------------------------------
# --------- Settings -----------
#-------------------------------

# FastAPI base settings
app = FastAPI(
    title="Verdikt",
    description="Hybrid static application analysis system based on CodeQL and LLM validation",
    version="0.0.1"
)

# Mounting HTML and CSS
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.mount("/script", StaticFiles(directory="app/script"), name="script")

# Init Interfaces
def get_scan_service() -> CodeQlScanInterface:
    return CodeQlScanService()

#------------------------------------
# ------------ Endpoints ------------
#------------------------------------

# Home
@app.get("/", response_class=HTMLResponse)
async def serve_home_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Main page"}
    )


# Scan Repo 
@app.post("/analyze/repo")
async def trigger_scan(payload: ScanRequest,
                       service: CodeQlScanInterface = Depends(get_scan_service)):    
    
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


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=11000, reload=True)
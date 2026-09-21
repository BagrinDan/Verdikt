# External
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI
from loguru import logger

# Internal
from app.controllers.pages.main_page import router as home_page
from app.controllers.api.scan_controller import router as codeql_scan

# ==============
# == Settings == 
# ==============
app = FastAPI(
    title="Verdikt",
    description="Hybrid static application analysis system based on CodeQL and LLM validation",
    version="0.0.1"
)

# =======================
# Mounting frontend stuff
# =======================
templates = Jinja2Templates(directory="app/templates") # HTML
app.mount("/static", StaticFiles(directory="app/static"), name="static") # CSS
app.mount("/script", StaticFiles(directory="app/script"), name="script") # Javastrip

# ======================
# Mounting backend stuff
# ======================
app.include_router(home_page)
app.include_router(codeql_scan)

# ====================
# Localserver settings
# ====================
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=11001, reload=True)
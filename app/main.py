import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI(
    title="Verdikt",
    description="Hybrid static application analysis system based on CodeQL and LLM validation",
    version="0.0.1"
)


app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def serve_home_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Main page"}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=11000, reload=True)
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .routers import health, jobs

app = FastAPI()

app.include_router(health.router)
app.include_router(jobs.router)


@app.get("/", include_in_schema=False)
async def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")
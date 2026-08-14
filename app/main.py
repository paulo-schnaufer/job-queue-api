from fastapi import FastAPI

from .routers import health, jobs

app = FastAPI()

app.include_router(health.router)
app.include_router(jobs.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
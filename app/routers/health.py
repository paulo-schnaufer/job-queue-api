from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("/")
async def read_health() -> dict[str, str]:
    return {"status": "ok"}
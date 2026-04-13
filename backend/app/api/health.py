from fastapi import APIRouter

router = APIRouter(prefix="/api/health")

@router.get("/ping")
async def ping():
    return {"ping": "pong"}

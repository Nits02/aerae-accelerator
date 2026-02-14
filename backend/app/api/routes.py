from fastapi import APIRouter

router = APIRouter(tags=["v1"])


@router.get("/")
async def root():
    return {"message": "AERAE Accelerator API v1"}

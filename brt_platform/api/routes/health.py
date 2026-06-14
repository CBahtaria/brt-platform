from fastapi import APIRouter

router = APIRouter(tags=["ops"])


@router.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}


@router.get("/")
async def root():
    return {"name": "BRT Platform", "version": "0.1.0", "docs": "/docs"}

from fastapi import APIRouter

router = APIRouter(
    prefix="/analytics",
    tags=["analytics-legacy"],
    deprecated=True,
)

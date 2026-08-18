from fastapi import APIRouter

router = APIRouter(
    prefix="/compliance",
    tags=["compliance-legacy"],
    deprecated=True,
)

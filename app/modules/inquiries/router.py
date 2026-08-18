from fastapi import APIRouter

router = APIRouter(
    prefix="/inquiries",
    tags=["inquiries-legacy"],
    deprecated=True,
)

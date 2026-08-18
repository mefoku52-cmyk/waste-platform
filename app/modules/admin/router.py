from fastapi import APIRouter

router = APIRouter(
    prefix="/admin",
    tags=["admin-legacy"],
    deprecated=True,
)

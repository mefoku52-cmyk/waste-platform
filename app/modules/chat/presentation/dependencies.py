"""chat dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.session import get_db_session

from ..application.services import ChatService
from ..infrastructure.repositories import ChatRepositoryImpl


def get_chat_service(session: AsyncSession = Depends(get_db_session)) -> ChatService:
    return ChatService(ChatRepositoryImpl(session))

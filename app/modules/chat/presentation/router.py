"""chat API router."""

from fastapi import APIRouter, Depends, Query

from app.shared.domain.exceptions import NotFoundDomainError
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.error_schemas import error_responses

from ..domain.entities import ChatMessageEntity, ChatThreadEntity
from .dependencies import get_chat_service
from .schemas import (
    ChatMessageData,
    ChatMessageResponse,
    ChatThreadData,
    ChatThreadResponse,
    CreateThreadRequest,
    PaginatedMessagesResponse,
    PaginatedThreadsResponse,
    PaginationMeta,
    SendMessageRequest,
    UnreadCountResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])


def _thread_data(e: ChatThreadEntity) -> ChatThreadData:
    return ChatThreadData(
        id=e.id,
        listingId=e.listing_id,
        initiatorUserId=e.initiator_user_id,
        initiatorCompanyId=e.initiator_company_id,
        recipientUserId=e.recipient_user_id,
        recipientCompanyId=e.recipient_company_id,
        subject=e.subject,
        status=e.status.value if hasattr(e.status, "value") else str(e.status),
        lastMessageAt=e.last_message_at,
        createdAt=e.created_at,
        updatedAt=e.updated_at,
    )


def _message_data(e: ChatMessageEntity) -> ChatMessageData:
    return ChatMessageData(
        id=e.id,
        threadId=e.thread_id,
        senderUserId=e.sender_user_id,
        senderCompanyId=e.sender_company_id,
        body=e.body,
        readAt=e.read_at,
        createdAt=e.created_at,
    )


def _user_id(current_user):
    u = getattr(current_user, "user", None)
    if u is not None:
        return getattr(u, "id", None)
    return getattr(current_user, "id", None)


@router.post(
    "/threads",
    response_model=ChatThreadResponse,
    status_code=201,
    responses=error_responses(401, 403, 422, 500),
)
async def create_thread(
    payload: CreateThreadRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_chat_service),
):
    uid = _user_id(current_user)
    thread = await service.create_thread(
        initiator_user_id=uid,
        initiator_company_id=payload.initiatorCompanyId,
        recipient_user_id=payload.recipientUserId,
        recipient_company_id=payload.recipientCompanyId,
        subject=payload.subject,
        listing_id=payload.listingId,
    )
    return ChatThreadResponse(data=_thread_data(thread))


@router.get(
    "/threads",
    response_model=PaginatedThreadsResponse,
    responses=error_responses(401, 500),
)
async def list_threads(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=50, ge=1, le=100),
    current_user=Depends(require_current_user),
    service=Depends(get_chat_service),
):
    uid = _user_id(current_user)
    detailed = await service.list_threads_detailed(uid, page, pageSize)
    total = await service.count_threads(uid)
    items = []
    for d in detailed:
        base = _thread_data(d["thread"])
        base.lastMessage = d["last_message"]
        base.unreadCount = d["unread_count"]
        base.counterpartUserId = d["counterpart_user_id"]
        items.append(base)
    return PaginatedThreadsResponse(
        items=items,
        meta=PaginationMeta(page=page, pageSize=pageSize, total=total),
    )


@router.get(
    "/threads/{thread_id}",
    response_model=ChatThreadResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def get_thread(
    thread_id: str,
    current_user=Depends(require_current_user),
    service=Depends(get_chat_service),
):
    uid = _user_id(current_user)
    thread = await service.get_thread(thread_id)
    if thread is None:
        raise NotFoundDomainError("Thread not found")
    if uid not in (thread.initiator_user_id, thread.recipient_user_id):
        raise NotFoundDomainError("Thread not found")
    return ChatThreadResponse(data=_thread_data(thread))


@router.get(
    "/threads/{thread_id}/messages",
    response_model=PaginatedMessagesResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def list_messages(
    thread_id: str,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=100, ge=1, le=200),
    current_user=Depends(require_current_user),
    service=Depends(get_chat_service),
):
    uid = _user_id(current_user)
    thread = await service.get_thread(thread_id)
    if thread is None:
        raise NotFoundDomainError("Thread not found")
    if uid not in (thread.initiator_user_id, thread.recipient_user_id):
        raise NotFoundDomainError("Thread not found")
    items = await service.list_messages(thread_id, page, pageSize)
    total = await service.repo.count_messages(thread_id)
    return PaginatedMessagesResponse(
        items=[_message_data(m) for m in items],
        meta=PaginationMeta(page=page, pageSize=pageSize, total=total),
    )


@router.post(
    "/threads/{thread_id}/messages",
    response_model=ChatMessageResponse,
    status_code=201,
    responses=error_responses(401, 403, 404, 422, 500),
)
async def send_message(
    thread_id: str,
    payload: SendMessageRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_chat_service),
    session=Depends(get_db_session),
):
    from uuid import uuid4

    uid = _user_id(current_user)
    thread = await service.get_thread(thread_id)
    if thread is None:
        raise NotFoundDomainError("Thread not found")

    msg = await service.send_message(
        thread_id=thread_id,
        sender_user_id=uid,
        sender_company_id=None,
        body=payload.body,
    )

    # Notifikacia pre prijemcu
    try:
        recipient_id = (
            thread.recipient_user_id
            if str(thread.initiator_user_id) == str(uid)
            else thread.initiator_user_id
        )

        from datetime import datetime as _dt

        from app.modules.notifications.domain.entities import NotificationEntity
        from app.modules.notifications.infrastructure.repositories import (
            NotificationRepositoryImpl,
        )

        notif = NotificationEntity(
            id=uuid4(),
            user_id=recipient_id,
            type="chat_message",
            title="Nova sprava v chate",
            message=payload.body[:200],
            is_read=False,
            related_entity_id=thread_id,
            created_at=_dt.now(),
            updated_at=_dt.now(),
            created_by_user_id=uid,
            updated_by_user_id=uid,
        )
        await NotificationRepositoryImpl(session).create(notif)
    except Exception:
        pass  # best-effort: never break caller

    return ChatMessageResponse(data=_message_data(msg))


@router.post(
    "/threads/{thread_id}/read",
    responses=error_responses(401, 403, 404, 500),
)
async def mark_read(
    thread_id: str,
    current_user=Depends(require_current_user),
    service=Depends(get_chat_service),
):
    uid = _user_id(current_user)
    count = await service.mark_read(thread_id, uid)
    return {"marked": count}


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    responses=error_responses(401, 500),
)
async def unread_count(
    current_user=Depends(require_current_user),
    service=Depends(get_chat_service),
):
    uid = _user_id(current_user)
    count = await service.unread_count(uid)
    return UnreadCountResponse(unread=count)

"""chat mappers."""

from app.modules.chat.domain.entities import ChatMessageEntity, ChatThreadEntity
from app.modules.chat.domain.enums import ChatThreadStatus
from app.modules.chat.infrastructure.models import ChatMessageModel, ChatThreadModel


def thread_to_domain(m: ChatThreadModel) -> ChatThreadEntity:
    return ChatThreadEntity(
        id=m.id,
        listing_id=m.listing_id,
        initiator_user_id=m.initiator_user_id,
        initiator_company_id=m.initiator_company_id,
        recipient_user_id=m.recipient_user_id,
        recipient_company_id=m.recipient_company_id,
        subject=m.subject,
        status=ChatThreadStatus(m.status),
        last_message_at=m.last_message_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
        created_by_user_id=m.created_by_user_id,
        updated_by_user_id=m.updated_by_user_id,
    )


def thread_to_model(e: ChatThreadEntity) -> ChatThreadModel:
    return ChatThreadModel(
        id=e.id,
        listing_id=e.listing_id,
        initiator_user_id=e.initiator_user_id,
        initiator_company_id=e.initiator_company_id,
        recipient_user_id=e.recipient_user_id,
        recipient_company_id=e.recipient_company_id,
        subject=e.subject,
        status=e.status.value,
        last_message_at=e.last_message_at,
        created_at=e.created_at,
        updated_at=e.updated_at,
        created_by_user_id=e.created_by_user_id,
        updated_by_user_id=e.updated_by_user_id,
    )


def message_to_domain(m: ChatMessageModel) -> ChatMessageEntity:
    return ChatMessageEntity(
        id=m.id,
        thread_id=m.thread_id,
        sender_user_id=m.sender_user_id,
        sender_company_id=m.sender_company_id,
        body=m.body,
        read_at=m.read_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
        created_by_user_id=m.created_by_user_id,
        updated_by_user_id=m.updated_by_user_id,
    )


def message_to_model(e: ChatMessageEntity) -> ChatMessageModel:
    return ChatMessageModel(
        id=e.id,
        thread_id=e.thread_id,
        sender_user_id=e.sender_user_id,
        sender_company_id=e.sender_company_id,
        body=e.body,
        read_at=e.read_at,
        created_at=e.created_at,
        updated_at=e.updated_at,
        created_by_user_id=e.created_by_user_id,
        updated_by_user_id=e.updated_by_user_id,
    )

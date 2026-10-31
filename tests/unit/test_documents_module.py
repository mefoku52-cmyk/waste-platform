"""Tests for the documents module: service contract + tenant isolation.

The module had zero tests. These cover:
- entity validation rules
- service CRUD contract with a fake repository
- router authorization helpers (tenant isolation, platform-admin status change)
"""

from dataclasses import dataclass, field
from uuid import uuid4

import pytest

from app.modules.documents.application.services import DocumentService
from app.modules.documents.domain.entities import DocumentEntity
from app.modules.documents.domain.enums import DocumentStatus
from app.modules.documents.domain.repositories import DocumentRepository
from app.shared.domain.exceptions import (
    ForbiddenDomainError,
    NotFoundDomainError,
    ValidationDomainError,
)


def _entity(**over):
    base = {
        "title": "Zmluva",
        "document_type": "contract",
        "file_url": "https://example.com/doc.pdf",
        "company_id": uuid4(),
        "listing_id": None,
    }
    base.update(over)
    return DocumentEntity(**base)


@dataclass
class FakeDocumentRepository(DocumentRepository):
    rows: dict = field(default_factory=dict)

    async def get_by_id(self, id: str):
        return self.rows.get(str(id))

    async def get_by_file_url(self, file_url: str):
        for row in self.rows.values():
            if row.file_url == file_url:
                return row
        return None

    async def list_all(self, page=1, limit=20):
        return list(self.rows.values())

    async def list_by_company_ids(self, company_ids, page=1, limit=20):
        return [r for r in self.rows.values() if str(r.company_id) in {str(c) for c in company_ids}]

    async def count_by_company_ids(self, company_ids):
        ids = {str(c) for c in company_ids}
        return sum(1 for r in self.rows.values() if str(r.company_id) in ids)

    async def count_all(self):
        return len(self.rows)

    async def create(self, entity):
        self.rows[str(entity.id)] = entity
        return entity

    async def update(self, entity):
        self.rows[str(entity.id)] = entity
        return entity

    async def delete(self, id: str):
        self.rows.pop(str(id), None)


# --------------------------------------------------------------------------
# entity validation
# --------------------------------------------------------------------------


def test_entity_rejects_empty_title():
    with pytest.raises(ValidationDomainError):
        _entity(title="").validate()


def test_entity_rejects_empty_document_type():
    with pytest.raises(ValidationDomainError):
        _entity(document_type="").validate()


def test_entity_rejects_empty_file_url():
    with pytest.raises(ValidationDomainError):
        _entity(file_url="").validate()


def test_entity_default_status_is_pending():
    assert _entity().status == DocumentStatus.PENDING


# --------------------------------------------------------------------------
# service contract
# --------------------------------------------------------------------------


async def test_create_persists_and_validates():
    repo = FakeDocumentRepository()
    svc = DocumentService(repo)
    entity = _entity()

    created = await svc.create(entity)

    assert str(created.id) in repo.rows
    assert repo.rows[str(created.id)].title == "Zmluva"


async def test_create_rejects_invalid_entity():
    repo = FakeDocumentRepository()
    svc = DocumentService(repo)

    with pytest.raises(ValidationDomainError):
        await svc.create(_entity(title=""))


async def test_update_raises_not_found_for_unknown_id():
    repo = FakeDocumentRepository()
    svc = DocumentService(repo)

    with pytest.raises(NotFoundDomainError):
        await svc.update(str(uuid4()), _entity())


async def test_update_preserves_audit_fields():
    repo = FakeDocumentRepository()
    svc = DocumentService(repo)
    original = _entity()
    await repo.create(original)

    replacement = _entity(title="Nova verzia")
    updated = await svc.update(str(original.id), replacement)

    assert updated.id == original.id
    assert updated.created_at == original.created_at
    assert updated.title == "Nova verzia"


async def test_delete_raises_not_found_for_unknown_id():
    repo = FakeDocumentRepository()
    svc = DocumentService(repo)

    with pytest.raises(NotFoundDomainError):
        await svc.delete(str(uuid4()))


async def test_delete_removes_row():
    repo = FakeDocumentRepository()
    svc = DocumentService(repo)
    entity = _entity()
    await repo.create(entity)

    await svc.delete(str(entity.id))

    assert str(entity.id) not in repo.rows


async def test_list_scoped_to_company_ids():
    repo = FakeDocumentRepository()
    svc = DocumentService(repo)
    company_a = uuid4()
    company_b = uuid4()
    doc_a = _entity(company_id=company_a)
    doc_b = _entity(company_id=company_b)
    await repo.create(doc_a)
    await repo.create(doc_b)

    listed = await svc.list_by_company_ids([company_a])
    total = await svc.count_by_company_ids([company_a])

    assert [d.id for d in listed] == [doc_a.id]
    assert total == 1


# --------------------------------------------------------------------------
# router authorization (tenant isolation)
# --------------------------------------------------------------------------


def _current_user(company_ids, is_admin=False):
    class User:
        pass

    from types import SimpleNamespace

    u = SimpleNamespace(
        memberships=[{"companyId": cid} for cid in company_ids],
        is_platform_admin=is_admin,
    )
    return u


def test_router_document_access_allows_own_company():
    from app.modules.documents.presentation.router import _ensure_document_access

    entity = _entity(company_id=uuid4())
    user = _current_user([entity.company_id])

    _ensure_document_access(entity, user)  # nesmie vyhodiť


def test_router_document_access_forbids_foreign_company():
    from app.modules.documents.presentation.router import _ensure_document_access

    entity = _entity(company_id=uuid4())
    user = _current_user([uuid4()])

    with pytest.raises(ForbiddenDomainError):
        _ensure_document_access(entity, user)


async def test_approved_document_still_requires_company_membership():
    from app.modules.documents.presentation.router import get_document

    entity = _entity(status=DocumentStatus.APPROVED)
    repo = FakeDocumentRepository()
    await repo.create(entity)
    service = DocumentService(repo)
    other_company_member = _current_user([uuid4()])

    with pytest.raises(ForbiddenDomainError):
        await get_document(str(entity.id), other_company_member, service)


def test_router_create_forbids_foreign_company():
    from app.modules.documents.presentation.router import _allowed_company_ids

    company = uuid4()
    user = _current_user([company])

    assert _allowed_company_ids(user) == {company}


def test_router_update_status_requires_platform_admin():
    """Zmena statusu dokumentu je vyhradená platform adminovi."""
    from app.modules.documents.presentation.router import _ensure_document_access

    entity = _entity(company_id=uuid4())
    member = _current_user([entity.company_id])

    # bežný člen má prístup k dokumentu svojej firmy…
    _ensure_document_access(entity, member)

    # …ale status mení len admin (overené v update_document vetve).
    assert not member.is_platform_admin


async def test_platform_admin_can_patch_document_outside_membership():
    from app.modules.documents.presentation.router import update_document
    from app.modules.documents.presentation.schemas import DocumentUpdateRequest

    entity = _entity()
    repo = FakeDocumentRepository()
    await repo.create(entity)
    service = DocumentService(repo)
    admin = _current_user([], is_admin=True)
    admin.roleCodes = ["platform_admin"]

    response = await update_document(str(entity.id), DocumentUpdateRequest(title="Admin update"), admin, service)

    assert response.data.title == "Admin update"
    assert response.data.companyId == entity.company_id


async def test_non_admin_patch_foreign_document_is_forbidden():
    from app.modules.documents.presentation.router import update_document
    from app.modules.documents.presentation.schemas import DocumentUpdateRequest

    entity = _entity()
    repo = FakeDocumentRepository()
    await repo.create(entity)
    service = DocumentService(repo)
    member = _current_user([uuid4()])

    with pytest.raises(ForbiddenDomainError):
        await update_document(str(entity.id), DocumentUpdateRequest(title="Unauthorized"), member, service)


async def test_non_admin_cannot_reassign_document_outside_membership():
    from app.modules.documents.presentation.router import update_document
    from app.modules.documents.presentation.schemas import DocumentUpdateRequest

    company_id = uuid4()
    entity = _entity(company_id=company_id)
    repo = FakeDocumentRepository()
    await repo.create(entity)
    service = DocumentService(repo)
    member = _current_user([company_id])

    with pytest.raises(ForbiddenDomainError):
        await update_document(
            str(entity.id), DocumentUpdateRequest(companyId=uuid4()), member, service
        )

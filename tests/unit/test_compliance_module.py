"""Tests for the compliance module: service contract + tenant isolation.

The module had zero tests. These cover:
- entity validation rules
- service CRUD contract with a fake repository
- router authorization helpers (tenant isolation, admin-only writes)
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

import pytest

from app.modules.compliance.application.services import ComplianceRecordService
from app.modules.compliance.domain.entities import ComplianceRecordEntity
from app.modules.compliance.domain.enums import ComplianceRecordStatus
from app.modules.compliance.domain.repositories import ComplianceRecordRepository
from app.shared.domain.exceptions import (
    ForbiddenDomainError,
    NotFoundDomainError,
    ValidationDomainError,
)


def _entity(**over):
    base = {
        "company_id": uuid4(),
        "regulation_type": "waste_register",
        "document_ref": "doc/ref",
        "valid_until": datetime(2027, 1, 1),
        "notes": "v poriadku",
    }
    base.update(over)
    return ComplianceRecordEntity(**base)


@dataclass
class FakeComplianceRepository(ComplianceRecordRepository):
    rows: dict = field(default_factory=dict)

    async def get_by_id(self, id: str):
        return self.rows.get(str(id))

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


def test_entity_rejects_empty_regulation_type():
    with pytest.raises(ValidationDomainError):
        _entity(regulation_type="").validate()


def test_entity_default_status_is_pending():
    assert _entity().status == ComplianceRecordStatus.PENDING


# --------------------------------------------------------------------------
# service contract
# --------------------------------------------------------------------------


async def test_create_persists():
    repo = FakeComplianceRepository()
    svc = ComplianceRecordService(repo)
    entity = _entity()

    created = await svc.create(entity)

    assert str(created.id) in repo.rows
    assert repo.rows[str(created.id)].regulation_type == "waste_register"


async def test_create_rejects_invalid_entity():
    repo = FakeComplianceRepository()
    svc = ComplianceRecordService(repo)

    with pytest.raises(ValidationDomainError):
        await svc.create(_entity(regulation_type=""))


async def test_update_raises_not_found_for_unknown_id():
    repo = FakeComplianceRepository()
    svc = ComplianceRecordService(repo)

    with pytest.raises(NotFoundDomainError):
        await svc.update(str(uuid4()), _entity())


async def test_update_preserves_audit_fields():
    repo = FakeComplianceRepository()
    svc = ComplianceRecordService(repo)
    original = _entity()
    await repo.create(original)

    replacement = _entity(notes="aktualizované")
    updated = await svc.update(str(original.id), replacement)

    assert updated.id == original.id
    assert updated.created_at == original.created_at
    assert updated.notes == "aktualizované"


async def test_delete_raises_not_found_for_unknown_id():
    repo = FakeComplianceRepository()
    svc = ComplianceRecordService(repo)

    with pytest.raises(NotFoundDomainError):
        await svc.delete(str(uuid4()))


async def test_list_scoped_to_company_ids():
    repo = FakeComplianceRepository()
    svc = ComplianceRecordService(repo)
    company_a = uuid4()
    company_b = uuid4()
    rec_a = _entity(company_id=company_a)
    rec_b = _entity(company_id=company_b)
    await repo.create(rec_a)
    await repo.create(rec_b)

    listed = await svc.list_by_company_ids([company_a])
    total = await svc.count_by_company_ids([company_a])

    assert [r.id for r in listed] == [rec_a.id]
    assert total == 1


async def test_tenant_cannot_see_other_companys_records():
    """Izolácia dát medzi firmami na service úrovni."""
    repo = FakeComplianceRepository()
    svc = ComplianceRecordService(repo)
    company_a = uuid4()
    company_b = uuid4()
    await repo.create(_entity(company_id=company_a))
    await repo.create(_entity(company_id=company_b))

    visible = await svc.list_by_company_ids([company_a])

    assert all(str(r.company_id) == str(company_a) for r in visible)


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


def test_router_access_requires_membership():
    from app.modules.compliance.presentation.router import _require_access

    entity = _entity(company_id=uuid4())
    user = _current_user([uuid4()])

    with pytest.raises(ForbiddenDomainError):
        _require_access(entity, user)


def test_router_access_allows_own_company_member():
    from app.modules.compliance.presentation.router import _require_access

    entity = _entity(company_id=uuid4())
    user = _current_user([entity.company_id])

    _require_access(entity, user)  # nesmie vyhodiť


def test_router_access_denies_companyless_record_to_tenant():
    from app.modules.compliance.presentation.router import _require_access

    entity = _entity(company_id=None)  # type: ignore[arg-type]
    user = _current_user([])

    with pytest.raises(ForbiddenDomainError):
        _require_access(entity, user)

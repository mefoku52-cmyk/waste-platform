"""Unit tests for listings entity validation."""

import pytest

from app.modules.listings.domain.entities import ListingsEntity
from app.modules.listings.domain.enums import ListingsStatus
from app.shared.domain.exceptions import ValidationDomainError


def _mk(**over):
    base = {
        "title": "Test",
        "material_type": "PET",
        "quantity": 10.0,
        "unit": "kg",
        "condition": "new",
        "location": "Bratislava",
        "company_id": "c-1",
        "status": ListingsStatus.DRAFT,
    }
    base.update(over)
    return ListingsEntity(**base)


def test_valid():
    _mk().validate()


def test_empty_title_raises():
    with pytest.raises(ValidationDomainError):
        _mk(title="").validate()


def test_empty_material_raises():
    with pytest.raises(ValidationDomainError):
        _mk(material_type="").validate()


def test_zero_quantity_raises():
    with pytest.raises(ValidationDomainError):
        _mk(quantity=0).validate()


def test_negative_quantity_raises():
    with pytest.raises(ValidationDomainError):
        _mk(quantity=-1).validate()


def test_missing_company_raises():
    with pytest.raises(ValidationDomainError):
        _mk(company_id="").validate()

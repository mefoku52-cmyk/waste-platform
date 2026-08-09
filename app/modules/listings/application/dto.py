"""listings DTOs."""

from dataclasses import dataclass


@dataclass
class ListingsCreateDTO:
    """Create listings DTO."""

    title: str
    material_type: str
    quantity: float
    unit: str
    condition: str
    location: str
    company_id: str
    price: float | None = None
    currency: str = "EUR"
    description: str | None = None


@dataclass
class ListingsUpdateDTO:
    """Update listings DTO."""

    title: str | None = None
    material_type: str | None = None
    quantity: float | None = None
    unit: str | None = None
    price: float | None = None
    currency: str | None = None
    condition: str | None = None
    location: str | None = None
    status: str | None = None
    description: str | None = None

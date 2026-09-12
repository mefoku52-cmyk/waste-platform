from uuid import UUID

from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.enums import CompanyStatus, CompanyType
from app.modules.companies.infrastructure.models import CompanyModel


def to_domain(model: CompanyModel) -> Company:
    return Company(
        id=UUID(model.id),
        status=CompanyStatus(model.status),
        legal_name=model.legal_name,
        trading_name=model.trading_name,
        registration_number=model.registration_number,
        tax_identifier=model.tax_identifier,
        company_type=CompanyType(model.company_type),
        email=model.email,
        phone=model.phone,
        website_url=model.website_url,
        country_code=model.country_code,
        address_line_1=model.address_line_1,
        address_line_2=model.address_line_2,
        city=model.city,
        postal_code=model.postal_code,
        latitude=model.latitude,
        longitude=model.longitude,
        seller_capability=model.seller_capability,
        buyer_capability=model.buyer_capability,
        logistics_capability=model.logistics_capability,
        verification_submitted_at=model.verification_submitted_at,
        verification_reviewed_at=model.verification_reviewed_at,
        verification_reviewed_by_user_id=UUID(model.verification_reviewed_by_user_id)
        if model.verification_reviewed_by_user_id
        else None,
        verified_at=model.verified_at,
        verified_by_user_id=UUID(model.verified_by_user_id) if model.verified_by_user_id else None,
        rejected_at=model.rejected_at,
        rejected_by_user_id=UUID(model.rejected_by_user_id) if model.rejected_by_user_id else None,
        created_at=model.created_at,
        created_by_user_id=UUID(model.created_by_user_id) if model.created_by_user_id else None,
        updated_at=model.updated_at,
        updated_by_user_id=UUID(model.updated_by_user_id) if model.updated_by_user_id else None,
    )


def to_model(entity: Company) -> CompanyModel:
    return CompanyModel(
        id=str(entity.id),
        status=entity.status.value,
        legal_name=entity.legal_name,
        trading_name=entity.trading_name,
        registration_number=entity.registration_number,
        tax_identifier=entity.tax_identifier,
        company_type=entity.company_type.value,
        email=entity.email,
        phone=entity.phone,
        website_url=entity.website_url,
        country_code=entity.country_code,
        address_line_1=entity.address_line_1,
        address_line_2=entity.address_line_2,
        city=entity.city,
        postal_code=entity.postal_code,
        latitude=entity.latitude,
        longitude=entity.longitude,
        seller_capability=entity.seller_capability,
        buyer_capability=entity.buyer_capability,
        logistics_capability=entity.logistics_capability,
        verification_submitted_at=entity.verification_submitted_at,
        verification_reviewed_at=entity.verification_reviewed_at,
        verification_reviewed_by_user_id=str(entity.verification_reviewed_by_user_id)
        if entity.verification_reviewed_by_user_id
        else None,
        verified_at=entity.verified_at,
        verified_by_user_id=str(entity.verified_by_user_id) if entity.verified_by_user_id else None,
        rejected_at=entity.rejected_at,
        rejected_by_user_id=str(entity.rejected_by_user_id) if entity.rejected_by_user_id else None,
        created_at=entity.created_at,
        created_by_user_id=str(entity.created_by_user_id) if entity.created_by_user_id else None,
        updated_at=entity.updated_at,
        updated_by_user_id=str(entity.updated_by_user_id) if entity.updated_by_user_id else None,
    )

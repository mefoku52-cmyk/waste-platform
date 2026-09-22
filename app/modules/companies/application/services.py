from uuid import UUID

from app.modules.companies.application.dto import CompanyDTO
from app.modules.companies.application.mappers import to_company_dto
from app.modules.companies.application.rpo import lookup_ico
from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.enums import CompanyStatus, CompanyType
from app.modules.companies.domain.repositories import CompanyRepository
from app.modules.company_memberships.domain.entities import CompanyMembership
from app.modules.company_memberships.domain.enums import (
    CompanyMembershipRole,
    CompanyMembershipStatus,
)
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import NotFoundDomainError


class CreateCompanyService:
    def __init__(
        self,
        repo: CompanyRepository,
        membership_repo,
        uuid_generator: UuidGenerator,
        clock: Clock,
    ):
        self.repo = repo
        self.membership_repo = membership_repo
        self.uuid_generator = uuid_generator
        self.clock = clock

    async def execute(
        self,
        *,
        legal_name: str,
        trading_name: str | None,
        registration_number: str,
        tax_identifier: str | None,
        vat_identifier: str | None = None,
        company_type: str,
        email: str | None,
        phone: str | None,
        website_url: str | None,
        country_code: str,
        address_line_1: str,
        address_line_2: str | None,
        city: str,
        postal_code: str,
        latitude: float | None,
        longitude: float | None,
        seller_capability: bool,
        buyer_capability: bool,
        logistics_capability: bool,
        actor_user_id: UUID | None,
    ) -> CompanyDTO:
        now = self.clock.now()
        rpo = lookup_ico(tax_identifier)
        if not rpo.get("exists"):
            raise ValueError("ICO_NOT_FOUND")
        company = Company(
            id=self.uuid_generator.new(),
            status=CompanyStatus.DRAFT,
            legal_name=legal_name,
            trading_name=trading_name,
            registration_number=registration_number,
            tax_identifier=tax_identifier,
            vat_identifier=vat_identifier,
            company_type=CompanyType(company_type),
            email=email,
            phone=phone,
            website_url=website_url,
            country_code=country_code.upper(),
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude,
            seller_capability=seller_capability,
            buyer_capability=buyer_capability,
            logistics_capability=logistics_capability,
            verification_submitted_at=None,
            verification_reviewed_at=None,
            verification_reviewed_by_user_id=None,
            verified_at=None,
            verified_by_user_id=None,
            rejected_at=None,
            rejected_by_user_id=None,
            created_at=now,
            created_by_user_id=actor_user_id,
            updated_at=now,
            updated_by_user_id=actor_user_id,
        )
        company.validate()
        await self.repo.add(company)

        if actor_user_id is not None:
            membership = CompanyMembership(
                id=self.uuid_generator.new(),
                status=CompanyMembershipStatus.ACTIVE,
                company_id=company.id,
                user_id=actor_user_id,
                membership_role=CompanyMembershipRole.OWNER,
                is_primary_contact=True,
                invited_at=now,
                joined_at=now,
                left_at=None,
                created_at=now,
                created_by_user_id=actor_user_id,
                updated_at=now,
                updated_by_user_id=actor_user_id,
            )
            membership.validate()
            await self.membership_repo.add(membership)

        return to_company_dto(company)


class GetCompanyService:
    def __init__(self, repo: CompanyRepository):
        self.repo = repo

    async def execute(self, company_id: UUID) -> CompanyDTO:
        company = await self.repo.get_by_id(company_id)
        if not company:
            raise NotFoundDomainError("Company not found")
        return to_company_dto(company)


class ListCompaniesService:
    def __init__(self, repo: CompanyRepository):
        self.repo = repo

    async def execute(
        self,
        *,
        status: str | None,
        company_type: str | None,
        seller_capability: bool | None,
        buyer_capability: bool | None,
        logistics_capability: bool | None,
        q: str | None,
        page: int,
        page_size: int,
        company_ids: list | None = None,
    ) -> tuple[list[CompanyDTO], int]:
        companies, total = await self.repo.list(
            status=status,
            company_type=company_type,
            seller_capability=seller_capability,
            buyer_capability=buyer_capability,
            logistics_capability=logistics_capability,
            q=q,
            page=page,
            page_size=page_size,
            company_ids=company_ids,
        )
        return [to_company_dto(company) for company in companies], total


class UpdateCompanyService:
    def __init__(self, repo: CompanyRepository, clock: Clock):
        self.repo = repo
        self.clock = clock

    async def execute(
        self,
        *,
        company_id: UUID,
        legal_name: str | None,
        trading_name: str | None,
        tax_identifier: str | None,
        vat_identifier: str | None = None,
        email: str | None,
        phone: str | None,
        website_url: str | None,
        address_line_1: str | None,
        address_line_2: str | None,
        city: str | None,
        postal_code: str | None,
        latitude: float | None,
        longitude: float | None,
        actor_user_id: UUID | None,
    ) -> CompanyDTO:
        company = await self.repo.get_by_id(company_id)
        if not company:
            raise NotFoundDomainError("Company not found")
        if legal_name is not None:
            company.legal_name = legal_name
        if trading_name is not None:
            company.trading_name = trading_name
        if tax_identifier is not None:
            company.tax_identifier = tax_identifier
        if vat_identifier is not None:
            company.vat_identifier = vat_identifier
        if email is not None:
            company.email = email
        if phone is not None:
            company.phone = phone
        if website_url is not None:
            company.website_url = website_url
        if address_line_1 is not None:
            company.address_line_1 = address_line_1
        if address_line_2 is not None:
            company.address_line_2 = address_line_2
        if city is not None:
            company.city = city
        if postal_code is not None:
            company.postal_code = postal_code
        if latitude is not None:
            company.latitude = latitude
        if longitude is not None:
            company.longitude = longitude
        company.updated_at = self.clock.now()
        company.updated_by_user_id = actor_user_id
        company.validate()
        await self.repo.update(company)
        return to_company_dto(company)


class TransitionCompanyStatusService:
    def __init__(self, repo: CompanyRepository, clock: Clock):
        self.repo = repo
        self.clock = clock

    async def execute(
        self, *, company_id: UUID, to_status: str, actor_user_id: UUID | None
    ) -> CompanyDTO:
        company = await self.repo.get_by_id(company_id)
        if not company:
            raise NotFoundDomainError("Company not found")

        target_status = CompanyStatus(to_status)
        company.transition_status(target_status)

        now = self.clock.now()
        if target_status == CompanyStatus.VERIFICATION_SUBMITTED:
            company.verification_submitted_at = now
        elif target_status == CompanyStatus.VERIFIED:
            company.verification_reviewed_at = now
            company.verification_reviewed_by_user_id = actor_user_id
            company.verified_at = now
            company.verified_by_user_id = actor_user_id
        elif target_status == CompanyStatus.REJECTED:
            company.verification_reviewed_at = now
            company.verification_reviewed_by_user_id = actor_user_id
            company.rejected_at = now
            company.rejected_by_user_id = actor_user_id

        company.updated_at = now
        company.updated_by_user_id = actor_user_id
        await self.repo.update(company)
        return to_company_dto(company)

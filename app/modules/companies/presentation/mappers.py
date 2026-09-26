from app.modules.companies.application.dto import CompanyDTO
from app.modules.companies.presentation.schemas import CompanyData


def to_company_data(dto: CompanyDTO) -> CompanyData:
    return CompanyData(
        id=dto.id,
        status=dto.status,
        legalName=dto.legal_name,
        tradingName=dto.trading_name,
        registrationNumber=dto.registration_number,
        taxIdentifier=dto.tax_identifier,
        subscriptionTier=dto.subscription_tier,
        companyType=dto.company_type,
        email=dto.email,
        phone=dto.phone,
        websiteUrl=dto.website_url,
        countryCode=dto.country_code,
        addressLine1=dto.address_line_1,
        addressLine2=dto.address_line_2,
        city=dto.city,
        postalCode=dto.postal_code,
        latitude=dto.latitude,
        longitude=dto.longitude,
        sellerCapability=dto.seller_capability,
        buyerCapability=dto.buyer_capability,
        logisticsCapability=dto.logistics_capability,
        verificationSubmittedAt=dto.verification_submitted_at,
        verificationReviewedAt=dto.verification_reviewed_at,
        verificationReviewedByUserId=dto.verification_reviewed_by_user_id,
        verifiedAt=dto.verified_at,
        verifiedByUserId=dto.verified_by_user_id,
        rejectedAt=dto.rejected_at,
        rejectedByUserId=dto.rejected_by_user_id,
        createdAt=dto.created_at,
        createdByUserId=dto.created_by_user_id,
        updatedAt=dto.updated_at,
        updatedByUserId=dto.updated_by_user_id,
    )

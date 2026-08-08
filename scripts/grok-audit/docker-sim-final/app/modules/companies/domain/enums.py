from enum import StrEnum


class CompanyStatus(StrEnum):
    DRAFT = "draft"
    VERIFICATION_SUBMITTED = "verification_submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class CompanyType(StrEnum):
    SELLER = "seller"
    BUYER = "buyer"
    SELLER_BUYER = "seller_buyer"
    LOGISTICS_PARTNER = "logistics_partner"

from enum import StrEnum


class CompanyMembershipStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    INACTIVE = "inactive"
    REMOVED = "removed"


class CompanyMembershipRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    COMPLIANCE_CONTACT = "compliance_contact"
    SALES_CONTACT = "sales_contact"
    LOGISTICS_CONTACT = "logistics_contact"
    VIEWER = "viewer"

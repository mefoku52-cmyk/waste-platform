"""compliance domain enums."""

from enum import Enum


class ComplianceRecordStatus(str, Enum):
    PENDING = "pending"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"

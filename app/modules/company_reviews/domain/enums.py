"""company_reviews domain enums."""

from enum import StrEnum


class ReviewStatus(StrEnum):
    """Stav moderácie recenzie.

    * ``pending`` — nová, čaká na schválenie (predvolené; chráni pred spamom).
    * ``approved`` — zverejnená na verejnej stránke.
    * ``rejected`` — zamietnutá moderátorom, nezobrazuje sa.
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

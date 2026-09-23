from __future__ import annotations

from abc import ABC, abstractmethod

PREDICTION_ENTITLEMENT = "prediction"


class PredictionEntitlementProvider(ABC):
    """
    Boundary for checking whether a principal is entitled to prediction.

    This intentionally does not implement subscription/payment logic.

    An existing CMEP entitlement system can later implement this
    interface without coupling the prediction module to billing.
    """

    @abstractmethod
    async def has_prediction_access(
        self,
        *,
        principal_id: str,
        company_id: str | None = None,
    ) -> bool:
        raise NotImplementedError

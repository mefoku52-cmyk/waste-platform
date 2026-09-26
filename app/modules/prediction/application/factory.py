from __future__ import annotations

from app.modules.prediction.application.baseline_provider import (
    BaselinePredictionProvider,
)
from app.modules.prediction.application.config import PredictionConfig
from app.modules.prediction.application.entitlements import (
    EnvironmentPredictionEntitlementProvider,
)
from app.modules.prediction.application.service import PredictionService


def create_prediction_service() -> PredictionService:
    """
    Create the safe default prediction service.

    The concrete provider can later be replaced here by:

        MLPredictionProvider
        RemotePredictionProvider
        LocalModelProvider
        ...

    without changing CMEP consumers.
    """

    config = PredictionConfig.from_environment()

    provider = BaselinePredictionProvider()
    entitlement_provider = EnvironmentPredictionEntitlementProvider()

    return PredictionService(
        provider=provider,
        entitlement_provider=entitlement_provider,
        config=config,
    )


def create_prediction_service_with_db(*, session) -> PredictionService:
    """Create a PredictionService backed by the database entitlement gate.

    Falls back to the environment provider if the DB layer is unavailable.
    Never raises on import-time issues.
    """
    from app.modules.companies.application.entitlements import (
        CompanyEntitlementService,
    )
    from app.modules.companies.infrastructure.repositories import (
        SqlAlchemyCompanyRepository,
    )
    from app.modules.prediction.application.entitlements import (
        DatabasePredictionEntitlementProvider,
    )

    try:
        company_repo = SqlAlchemyCompanyRepository(session)
        company_entitlements = CompanyEntitlementService(repository=company_repo)
        entitlement_provider = DatabasePredictionEntitlementProvider(
            company_entitlement_service=company_entitlements,
        )
    except Exception:
        entitlement_provider = EnvironmentPredictionEntitlementProvider()

    config = PredictionConfig.from_environment()
    provider = BaselinePredictionProvider()

    return PredictionService(
        provider=provider,
        entitlement_provider=entitlement_provider,
        config=config,
    )

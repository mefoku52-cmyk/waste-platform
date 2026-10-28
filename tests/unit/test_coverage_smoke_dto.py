"""Smoke coverage: import low-coverage dto/mapper/enum modules."""

import importlib

MODULES = [
    "app.modules.admin.application.dto",
    "app.modules.admin.presentation.mappers",
    "app.modules.agent_platform.domain.agent.agent_capability",
    "app.modules.agent_platform.domain.policy.policy_rule",
    "app.modules.analytics.application.dto",
    "app.modules.analytics.domain.enums",
    "app.modules.analytics.presentation.mappers",
    "app.modules.compliance.application.dto",
    "app.modules.compliance.presentation.mappers",
    "app.modules.documents.application.dto",
    "app.modules.documents.presentation.mappers",
    "app.modules.inquiries.application.dto",
    "app.modules.inquiries.presentation.mappers",
    "app.modules.listings.domain.legal_regime",
    "app.modules.listings.presentation.mappers",
    "app.modules.notifications.application.dto",
    "app.modules.notifications.domain.enums",
    "app.modules.prediction.application.model_exports",
    "app.modules.prediction.application.recommendation_exports",
    "app.modules.prediction.domain.model_exports",
    "app.modules.prediction.domain.recommendation_exports",
    "app.modules.recommendations.application.email_templates",
]


def test_smoke_imports():
    for m in MODULES:
        mod = importlib.import_module(m)
        assert mod is not None

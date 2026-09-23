from __future__ import annotations


class FeatureNames:
    """
    Canonical feature names.

    Keep names stable once real models start consuming them.

    New features should be added here rather than scattering arbitrary
    string literals through prediction code.
    """

    # Listing identity / classification
    MATERIAL_TYPE = "material_type"
    CATEGORY = "category"
    LOCATION = "location"

    # Listing activity
    LISTING_VIEWS = "listing_views"
    LISTING_CLICKS = "listing_clicks"
    LISTING_SAVES = "listing_saves"

    # Commercial activity
    INQUIRY_COUNT = "inquiry_count"
    MATCH_COUNT = "match_count"
    RECOMMENDATION_COUNT = "recommendation_count"

    # Outcome signals
    DEAL_COUNT = "deal_count"
    COMPLETION_COUNT = "completion_count"

    # Temporal signals
    DAYS_ACTIVE = "days_active"
    DAYS_SINCE_ACTIVITY = "days_since_activity"

    # Company signals
    COMPANY_ACTIVITY = "company_activity"
    COMPANY_LISTING_COUNT = "company_listing_count"

    # Geographic signals
    DISTANCE_KM = "distance_km"

    # Matching signals
    MATERIAL_MATCH = "material_match"
    LOCATION_MATCH = "location_match"

    # Data quality
    DATA_COMPLETENESS = "data_completeness"

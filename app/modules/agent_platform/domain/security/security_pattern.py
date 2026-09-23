"""Security pattern categories."""

from enum import Enum


class SecurityPattern(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    MANIPULATION = "manipulation"
    SOCIAL_ENGINEERING = "social_engineering"
    COERCION = "coercion"
    DATA_LEAKAGE = "data_leakage"
    PERMISSION_ESCALATION = "permission_escalation"
    UNUSUAL_ACTIVITY = "unusual_activity"
    REPEATED_BEHAVIOR = "repeated_behavior"
    TOOL_ABUSE = "tool_abuse"
    AUTH_ANOMALY = "auth_anomaly"

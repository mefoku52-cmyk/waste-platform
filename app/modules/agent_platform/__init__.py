"""CMEP Agent Platform.

The Agent Platform is the controlled orchestration layer between AI agents
and existing CMEP business capabilities.

Important architectural rule:

    AI != AUTHORITY
    AI = AGENT

The module must not bypass authentication, authorization, policy, approval,
audit, or existing business services.
"""

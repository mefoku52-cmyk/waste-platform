"""Tests for agent gate / control mode."""

from app.modules.agent_platform.domain.control.agent_gate import (
    MUTATING_CLIENT_ACTIONS,
    resolve_agent_gate,
)
from app.modules.agent_platform.domain.control.control_mode import ControlMode


def test_normal_allows_everything():
    g = resolve_agent_gate(ControlMode.NORMAL)
    assert g.allowed is True
    assert g.allow_mutations is True
    assert g.allows_client_action("fill_form_field") is True
    assert g.allows_client_action("navigate") is True


def test_read_only_allows_read_but_blocks_mutating_client_action():
    g = resolve_agent_gate(ControlMode.READ_ONLY)
    assert g.allowed is True
    assert g.allow_mutations is False
    assert g.allows_client_action("fill_form_field") is False
    assert g.allows_client_action("navigate") is True
    assert g.allows_client_action("show_toast") is True


def test_ai_disabled_blocks_all():
    g = resolve_agent_gate(ControlMode.AI_DISABLED)
    assert g.allowed is False
    assert g.allow_mutations is False
    assert g.allows_client_action("navigate") is False


def test_lockdown_blocks_all():
    g = resolve_agent_gate(ControlMode.LOCKDOWN)
    assert g.allowed is False


def test_emergency_blocks_all():
    g = resolve_agent_gate(ControlMode.EMERGENCY)
    assert g.allowed is False


def test_mutating_actions_are_documented():
    assert "fill_form_field" in MUTATING_CLIENT_ACTIONS

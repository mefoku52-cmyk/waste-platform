"""Rate limit middleware _match_rule — pure unit tests."""

from app.shared.presentation.rate_limit_middleware import (
    RateLimitMiddleware,
    _match_rule,
    _normalize_path,
)


def test_normalize_removes_api_v1_prefix():
    assert _normalize_path("/api/v1/auth/login") == "/auth/login"


def test_normalize_keeps_plain_path():
    assert _normalize_path("/auth/login") == "/auth/login"


def test_normalize_handles_api_prefix_only():
    assert _normalize_path("/api/v1") == "/"
    assert _normalize_path("/api") == "/"


def test_match_2fa_login():
    rule = _match_rule("POST", "/api/v1/auth/2fa/login")
    assert rule is not None
    limit, period, name = rule
    assert name == "2fa-login-ip"
    assert limit == 10
    assert period == 60


def test_match_login_not_limited_in_middleware():
    """Login je limitovaný v handleri, nie middleware."""
    rule = _match_rule("POST", "/api/v1/auth/login")
    assert rule is None


def test_match_control_mode():
    rule = _match_rule("POST", "/api/v1/agent-platform/control/mode")
    assert rule is not None
    assert rule[2] == "control-mode"


def test_match_emergency_activate():
    rule = _match_rule("POST", "/api/v1/agent-platform/control/emergency/activate")
    assert rule is not None
    assert rule[2] == "control-emergency-activate"
    assert rule[0] == 5


def test_match_emergency_release():
    rule = _match_rule("POST", "/api/v1/agent-platform/control/emergency/release")
    assert rule is not None
    assert rule[2] == "control-emergency-release"


def test_match_admin_get_read():
    rule = _match_rule("GET", "/api/v1/admin/stats")
    assert rule is not None
    assert rule[2] == "admin-read"


def test_match_admin_post_write():
    rule = _match_rule("POST", "/api/v1/admin/lead-outreach/send")
    assert rule is not None
    assert rule[2] == "admin-write"


def test_match_chat_create():
    rule = _match_rule("POST", "/api/v1/chat/threads")
    assert rule is not None
    assert rule[2] == "chat-create"
    assert rule[0] == 30


def test_match_chat_message():
    rule = _match_rule("POST", "/api/v1/chat/threads/abc-123/messages")
    assert rule is not None
    assert rule[2] == "chat-message"


def test_match_uploads():
    rule = _match_rule("POST", "/api/v1/uploads/")
    assert rule is not None
    assert rule[2] == "uploads"


def test_match_listings_create():
    rule = _match_rule("POST", "/api/v1/listings")
    assert rule is not None
    assert rule[2] == "listings-create"


def test_match_listings_patch():
    rule = _match_rule("PATCH", "/api/v1/listings/some-id")
    assert rule is not None
    assert rule[2] == "listings-write"


def test_match_listings_delete():
    rule = _match_rule("DELETE", "/api/v1/listings/some-id")
    assert rule is not None
    assert rule[2] == "listings-delete"


def test_match_inquiries_create():
    rule = _match_rule("POST", "/api/v1/inquiries")
    assert rule is not None
    assert rule[2] == "inquiries-create"


def test_match_users_register():
    rule = _match_rule("POST", "/api/v1/users")
    assert rule is not None
    assert rule[2] == "user-register-ip"
    assert rule[0] == 3
    assert rule[1] == 3600


def test_no_match_health_endpoint():
    assert _match_rule("GET", "/health") is None


def test_no_match_get_public_endpoints():
    assert _match_rule("GET", "/api/v1/listings") is None


def test_no_match_wrong_method_for_rule():
    """GET /admin/ má read pravidlo, ale DELETE /admin/ má write pravidlo."""
    rule = _match_rule("OPTIONS", "/api/v1/admin/stats")
    assert rule is None


def test_middleware_class_exists():
    assert RateLimitMiddleware is not None

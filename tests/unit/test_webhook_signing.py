"""Unit tests for webhook HMAC signing and replay protection."""

import time

from app.modules.webhooks.infrastructure.signing import sign_payload, verify_signature


def test_sign_and_verify():
    secret = "test-secret"
    payload = {"event": "listing.created", "id": "123"}
    signature, ts = sign_payload(secret, payload)
    assert verify_signature(secret, payload, signature, ts)


def test_replay_protection():
    secret = "test-secret"
    payload = {"event": "test"}
    signature, ts = sign_payload(secret, payload, timestamp=int(time.time()) - 400)
    assert not verify_signature(secret, payload, signature, ts, tolerance=300)


def test_wrong_secret():
    payload = {"a": 1}
    signature, ts = sign_payload("correct", payload)
    assert not verify_signature("wrong", payload, signature, ts)
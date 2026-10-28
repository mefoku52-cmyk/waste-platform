from app.modules.prediction.infrastructure.outcome_repository import OutcomeRepository


def test_identifier_valid():
    assert OutcomeRepository._identifier("foo") == '"foo"'
    assert OutcomeRepository._identifier("a_b1") == '"a_b1"'


def test_identifier_invalid():
    import pytest

    with pytest.raises(ValueError):
        OutcomeRepository._identifier("")
    with pytest.raises(ValueError):
        OutcomeRepository._identifier("foo;drop")
    with pytest.raises(ValueError):
        OutcomeRepository._identifier("foo-bar")

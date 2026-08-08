from app.shared.domain.exceptions import InvalidTransitionDomainError


def ensure_transition(current: str, target: str, allowed: set[str]) -> None:
    if target not in allowed:
        raise InvalidTransitionDomainError(
            message=f"Invalid transition from {current} to {target}",
            current_status=current,
            attempted_status=target,
            allowed_transitions=sorted(list(allowed)),
        )

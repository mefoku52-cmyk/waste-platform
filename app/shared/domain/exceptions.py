class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ValidationDomainError(DomainError):
    code = "validation_error"


class NotFoundDomainError(DomainError):
    code = "not_found"


class ConflictDomainError(DomainError):
    code = "conflict"


class UnauthorizedDomainError(DomainError):
    code = "unauthorized"


class ForbiddenDomainError(DomainError):
    code = "forbidden"


class InvalidTransitionDomainError(DomainError):
    code = "invalid_transition"

    def __init__(
        self,
        message: str,
        current_status: str,
        attempted_status: str,
        allowed_transitions: list[str],
    ):
        self.current_status = current_status
        self.attempted_status = attempted_status
        self.allowed_transitions = allowed_transitions
        super().__init__(message)

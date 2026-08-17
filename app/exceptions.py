class DomainError(Exception):
    """Base for business errors, with no notion of HTTP."""


class UserAlreadyExists(DomainError):
    pass


class UserNotFound(DomainError):
    pass


class NotEnoughPermissions(DomainError):
    pass


class InvalidCredentials(DomainError):
    pass

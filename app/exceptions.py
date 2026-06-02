class AppError(Exception):
    """Base application exception."""

    pass


class EmailAlreadyExistsError(AppError):
    """Raised when an email is already registered."""

    def __init__(self, email: str):
        super().__init__(f"Email '{email}' is already registered.")
        self.email = email


class FirmNameAlreadyExistsError(AppError):
    """Raised when a firm name is already registered."""

    def __init__(self, name: str):
        super().__init__(f"Firm name '{name}' is already registered.")
        self.name = name


class InvalidCredentialsError(AppError):
    """Raised when login credentials are incorrect."""

    def __init__(self) -> None:
        super().__init__("Incorrect email or password.")


class InactiveUserError(AppError):
    """Raised when an inactive user attempts to authenticate."""

    def __init__(self) -> None:
        super().__init__("User account is inactive.")

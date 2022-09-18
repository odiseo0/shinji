class DAOExceptionBase(Exception):
    def __init__(self, status_code: int, detail: str | None = None) -> None:
        self.status_code = status_code
        self.detail = detail

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(status_code={self.status_code}, detail={self.detail})"


class DAOConflictException(DAOExceptionBase):
    """Exception raised when an `IntegrityError` occurs."""

    def __init__(
        self, status_code: int = 409, detail: str | None = "Conflict."
    ) -> None:
        super().__init__(status_code, detail)

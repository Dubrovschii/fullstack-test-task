"""Domain errors.  They know nothing about HTTP; the api layer maps them to status codes."""


class DomainError(Exception):
    detail = "Internal error"

    def __init__(self) -> None:
        super().__init__(self.detail)


class FileNotFound(DomainError):
    detail = "File not found"


class StoredFileMissing(DomainError):
    detail = "Stored file not found"


class EmptyFile(DomainError):
    detail = "File is empty"

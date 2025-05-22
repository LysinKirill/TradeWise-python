from app.domain.exceptions.validation.ValidationErrorCode import ValidationErrorCode


class ValidationException(Exception):
    def __init__(
            self,
            code: ValidationErrorCode,
            message: str
    ):
        self.code = code
        self.message = message

    def __str__(self):
        return self.message
from app.domain.exceptions.validation.ValidationErrorCode import ValidationErrorCode
from app.domain.exceptions.validation.ValidationException import ValidationException


class AllowedTimeIntervalExceeded(ValidationException):
    def __init__(
            self,
            allowed_time_seconds: int,
            actual_time_seconds: int
    ):
        message = f"Requested time interval ({actual_time_seconds} seconds) exceeds allowed time interval ({allowed_time_seconds} seconds)"
        super().__init__(
            ValidationErrorCode.AllowedTimeIntervalExceeded,
            message
        )
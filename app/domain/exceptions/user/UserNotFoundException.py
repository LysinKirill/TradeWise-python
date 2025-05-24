from app.domain.BusinessErrorCode import BusinessErrorCode
from app.domain.BusinessException import BusinessException


class UserNotFoundException(BusinessException):
    def __init__(
            self,
            source: str,
            user_id: int | None = None,
            user_email: str | None = None,
    ):
        if user_id is None and user_email is None:
            raise ValueError("At least one of user_id or user_email must be provided")

        by_clause: str
        if user_id is not None and user_email is not None:
            by_clause = f"by id ({user_id}) and email ({user_email})"
        elif user_id is not None:
            by_clause = f"by id ({user_id})"
        else:
            by_clause = f"by email ({user_email})"

        message = f"User not found {by_clause} in source {source}"
        super().__init__(BusinessErrorCode.UserNotFound, message)

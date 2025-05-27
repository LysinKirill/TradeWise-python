from app.domain.BusinessErrorCode import BusinessErrorCode
from app.domain.BusinessException import BusinessException


class InvestApiKeyNotSetException(BusinessException):
    def __init__(
            self,
            user_id: int
    ):
        message = f"Invest API key is not set for user {user_id}"
        super().__init__(BusinessErrorCode.InvestApiKeyNotSet, message)

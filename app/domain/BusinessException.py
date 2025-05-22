from app.domain.BusinessErrorCode import BusinessErrorCode


class BusinessException(Exception):
    def __init__(
            self,
            code: BusinessErrorCode,
            message: str
    ):
        self.code = code
        self.message = message

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message
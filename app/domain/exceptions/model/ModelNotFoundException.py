from app.domain.BusinessErrorCode import BusinessErrorCode
from app.domain.BusinessException import BusinessException


class ModelNotFoundException(BusinessException):
    def __init__(
            self,
            model_id: int,
            model_source: str | None = None
    ):
        message = f'Model {model_id} not found' if not model_source else f'Model {model_id} not found in source {model_source}'
        super().__init__(BusinessErrorCode.ModelNotFound, message)

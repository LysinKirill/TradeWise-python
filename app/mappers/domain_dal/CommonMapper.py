from app.domain.models.ml_model.ShortModelInfoModel import ShortModelInfoModel
from app.domain.models.user.UserInfoModel import UserInfoModel
from dataAccess.models.common.UserInfo import UserInfo
from dataAccess.models.model.ShortModelInfo import ShortModelInfo


class CommonMapper:
    @staticmethod
    def get_domain_model(db_model: ShortModelInfo) -> ShortModelInfoModel:
        return ShortModelInfoModel(
            id=db_model.id,
            instrument_id=db_model.instrument_id,
            name=db_model.name,
            model_type=db_model.model_type,
            created_at=db_model.created_at,
        )

    @staticmethod
    def get_domain_user(db_user: UserInfo) -> UserInfoModel:
        return UserInfoModel(
            id=db_user.id,
            email=db_user.email,
            invest_api_key=db_user.invest_api_key,
            invest_account_id=db_user.invest_account_id,
        )

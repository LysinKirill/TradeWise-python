from abc import ABC, abstractmethod
from dataAccess.models.common.UserInfo import UserInfo


class IUserRepository(ABC):
    @abstractmethod
    async def add_invest_api_key(self, email: str, api_key: str, invest_account_id: str) -> bool:
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> UserInfo | None:
        pass
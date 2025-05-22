from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    async def add_invest_api_key(self, email: str, api_key: str, invest_account_id: str) -> bool:
        pass
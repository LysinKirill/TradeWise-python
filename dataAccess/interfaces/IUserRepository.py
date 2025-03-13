from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    def add_invest_api_key(self, email: str, api_key: str) -> bool:
        pass
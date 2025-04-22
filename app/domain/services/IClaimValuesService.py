from abc import ABC, abstractmethod


class IClaimValuesService(ABC):
    @abstractmethod
    async def get_email(self) -> str | None:
        pass

from abc import ABC, abstractmethod


class IClaimValuesService(ABC):
    @abstractmethod
    def get_email(self) -> str | None:
        pass

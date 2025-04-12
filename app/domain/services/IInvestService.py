from abc import ABC, abstractmethod

from app.domain.models.invest.responses import GetSupportedInstrumentsResponseModel


class IInvestService(ABC):
    @abstractmethod
    def get_supported_instruments(self) -> GetSupportedInstrumentsResponseModel.GetSupportedInstrumentsResponseModel:
        pass

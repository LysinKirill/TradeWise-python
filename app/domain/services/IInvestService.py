from abc import ABC, abstractmethod

from app.domain.models.invest.requests.GetInstrumentStatRequestModel import GetInstrumentStatRequestModel
from app.domain.models.invest.responses.GetInstrumentStatResponseModel import GetInstrumentStatResponseModel
from app.domain.models.invest.responses.GetSupportedInstrumentsResponseModel import GetSupportedInstrumentsResponseModel


class IInvestService(ABC):
    @abstractmethod
    def get_supported_instruments(self) -> GetSupportedInstrumentsResponseModel:
        pass

    @abstractmethod
    def get_instrument_stat(self, request: GetInstrumentStatRequestModel) -> GetInstrumentStatResponseModel:
        pass

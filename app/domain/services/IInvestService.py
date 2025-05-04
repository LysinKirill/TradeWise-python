from abc import ABC, abstractmethod

from app.domain.models.invest.requests.GetCandlesRequestModel import GetCandlesRequestModel
from app.domain.models.invest.responses.GetCandlesResponseModel import GetCandlesResponseModel
from app.domain.models.invest.requests.GetInstrumentStatRequestModel import GetInstrumentStatRequestModel
from app.domain.models.invest.responses.GetInstrumentStatResponseModel import GetInstrumentStatResponseModel
from app.domain.models.invest.responses.GetSupportedInstrumentsResponseModel import GetSupportedInstrumentsResponseModel


class IInvestService(ABC):
    @abstractmethod
    async def get_supported_instruments(self) -> GetSupportedInstrumentsResponseModel:
        pass

    @abstractmethod
    async def get_instrument_stat(self, request: GetInstrumentStatRequestModel) -> GetInstrumentStatResponseModel:
        pass

    @abstractmethod
    async def get_candles(self, request: GetCandlesRequestModel) -> GetCandlesResponseModel:
        pass

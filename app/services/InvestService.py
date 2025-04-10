from app.domain.models.invest import RiskLevelModel
from app.domain.models.invest.InstrumentModel import InstrumentModel
from app.domain.models.invest.responses.GetSupportedInstrumentsResponseModel import GetSupportedInstrumentsResponseModel
from app.domain.services.IInvestService import IInvestService

from externalClients.TInvestApi.handlers.InstrumentsClient import InstrumentsClient


class InvestService(IInvestService):
    def __init__(
        self,
        instruments_client: InstrumentsClient
    ):
        self.instruments_client = instruments_client

    def get_supported_instruments(self) -> GetSupportedInstrumentsResponseModel:
        client_response = self.instruments_client.get_instruments()
        return GetSupportedInstrumentsResponseModel(
            instruments=list(map(InvestService.__get_instrument, client_response.instruments))
        )

    @staticmethod
    def __get_instrument(client_instrument) -> InstrumentModel:
        return InstrumentModel(
            id = client_instrument.id,
            figi = client_instrument.figi,
            name = client_instrument.name,
            lot = client_instrument.lot,
            currency = client_instrument.currency,
            sector = client_instrument.sector,
            buy_available = client_instrument.buy_available,
            sell_available = client_instrument.sell_available,
            risk_level = InvestService.__get_risk_level(client_instrument.risk_level),
        )

    @staticmethod
    def __get_risk_level(client_risk_level) -> RiskLevelModel.RiskLevelModel:
        return RiskLevelModel.RiskLevelModel(client_risk_level)
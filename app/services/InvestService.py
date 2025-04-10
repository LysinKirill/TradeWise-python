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
        supported_instruments_ids = ['03b320aa-6afd-46e5-b0f3-b60475070e9d', '3289e00a-ac43-458f-92aa-7da4bbb0f14f', 'cf331b84-b924-48f3-8878-4643047d5946', 'f1f307fd-7826-4fd8-a2a1-019bcaad4e72', 'abf46047-f3d8-4b1b-a33f-9aeed753cc02']
        client_response_instruments = self.instruments_client.get_instruments(supported_instruments_ids)
        return GetSupportedInstrumentsResponseModel(
            instruments=list(map(InvestService.__get_instrument, client_response_instruments))
        )

    @staticmethod
    def __get_instrument(client_instrument) -> InstrumentModel:
        return InstrumentModel(
            id = client_instrument.uid,
            figi = client_instrument.figi,
            name = client_instrument.name,
            lot = client_instrument.lot,
            currency = client_instrument.currency,
            sector = client_instrument.sector,
            buy_available = client_instrument.buy_available_flag,
            sell_available = client_instrument.sell_available_flag,
            risk_level = InvestService.__get_risk_level(client_instrument.risk_level),
        )

    @staticmethod
    def __get_risk_level(client_risk_level) -> RiskLevelModel.RiskLevelModel:
        return RiskLevelModel.RiskLevelModel(client_risk_level)
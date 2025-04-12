from app.configuration.SupportedInstrumentsOptions import SupportedInstrumentsOptions
from app.domain.models.invest.InstrumentModel import InstrumentModel
from app.domain.models.invest.responses.GetSupportedInstrumentsResponseModel import GetSupportedInstrumentsResponseModel
from app.domain.services.IInvestService import IInvestService

from externalClients.TInvestApi.handlers.InstrumentsClient import InstrumentsClient


class InvestService(IInvestService):
    def __init__(
        self,
        instruments_client: InstrumentsClient,
        supported_instruments_options: SupportedInstrumentsOptions
    ):
        self.instruments_client = instruments_client
        self.supported_instruments_options = supported_instruments_options

    def get_supported_instruments(self) -> GetSupportedInstrumentsResponseModel:
        supported_instruments_ids = self.supported_instruments_options.shares
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
            sell_available = client_instrument.sell_available_flag
        )
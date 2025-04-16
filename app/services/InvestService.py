from app.configuration.SupportedInstrumentsOptions import SupportedInstrumentsOptions
from app.domain.models.invest.InstrumentModel import InstrumentModel
from app.domain.models.invest.requests.GetInstrumentStatRequestModel import GetInstrumentStatRequestModel
from app.domain.models.invest.responses.GetInstrumentStatResponseModel import GetInstrumentStatResponseModel
from app.domain.models.invest.responses.GetSupportedInstrumentsResponseModel import GetSupportedInstrumentsResponseModel
from app.domain.services.IInvestService import IInvestService
from externalClients.TInvestApi.handlers import MarketDataClient

from externalClients.TInvestApi.handlers.InstrumentsClient import InstrumentsClient


class InvestService(IInvestService):
    def __init__(
        self,
        instruments_client: InstrumentsClient,
        marketdata_client: MarketDataClient,
        supported_instruments_options: SupportedInstrumentsOptions
    ):
        self.instruments_client = instruments_client
        self.supported_instruments_options = supported_instruments_options
        self.marketdata_client = marketdata_client

    def get_supported_instruments(self) -> GetSupportedInstrumentsResponseModel:
        supported_instruments_ids = self.supported_instruments_options.shares
        client_response_instruments = self.instruments_client.get_instruments(supported_instruments_ids)
        return GetSupportedInstrumentsResponseModel(
            instruments=list(map(InvestService.__get_instrument, client_response_instruments))
        )

    def get_instrument_stat(self, request: GetInstrumentStatRequestModel) -> GetInstrumentStatResponseModel:
        client_response_stat = self.marketdata_client.get_instrument_stat(request)
        stat = client_response_stat[0]
        return GetInstrumentStatResponseModel(0)




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
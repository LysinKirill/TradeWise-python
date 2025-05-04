from app.configuration.SupportedInstrumentsOptions import SupportedInstrumentsOptions
from app.domain.models.invest.CandleModel import CandleModel
from app.domain.models.invest.InstrumentModel import InstrumentModel
from app.domain.models.invest.requests.GetCandlesRequestModel import GetCandlesRequestModel
from app.domain.models.invest.requests.GetInstrumentStatRequestModel import GetInstrumentStatRequestModel
from app.domain.models.invest.responses.GetCandlesResponseModel import GetCandlesResponseModel
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

    async def get_supported_instruments(self) -> GetSupportedInstrumentsResponseModel:
        supported_instruments_ids = self.supported_instruments_options.shares
        client_response_instruments = await self.instruments_client.get_instruments(supported_instruments_ids)
        return GetSupportedInstrumentsResponseModel(
            instruments=list(map(InvestService.__get_instrument, client_response_instruments))
        )

    async def get_instrument_stat(self, request: GetInstrumentStatRequestModel) -> GetInstrumentStatResponseModel:
        client_response_stat = await self.marketdata_client.get_instrument_stat(request)
        return GetInstrumentStatResponseModel(stat_value=client_response_stat)

    async def get_candles(self, request: GetCandlesRequestModel) -> GetCandlesResponseModel:
        client_response = await self.marketdata_client.get_candles(request)
        return GetCandlesResponseModel(
            candles=list(map(lambda x: CandleModel(
                open=x[0],
                high=x[1],
                low=x[2],
                close=x[3],
                timestamp=x[4]
            ), client_response))
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
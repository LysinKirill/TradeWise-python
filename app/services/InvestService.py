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
        supported_instruments_ids = [
            'e6123145-9665-43e0-8413-cd61b8aa9b13',
            '962e2a95-02a9-4171-abd7-aa198dbe643a',
            '509edd0c-129c-4ee2-934d-7f6246126da1',
            '7de75794-a27f-4d81-a39b-492345813822',
            '02cfdf61-6298-4c0f-a9ca-9cabc82afaf3'
        ]
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
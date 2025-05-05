from ml.data.interface.IBroker import IBroker
from ml.data.model.OperationType import OperationType
from ml.data.model.responses.GetPortfolioResponse import GetPortfolioResponse
from grpc import aio, ssl_channel_credentials
from datetime import datetime
import logging
import sys

from externalClients.TInvestApi.proto import (
    common_pb2,
    orders_pb2,
    orders_pb2_grpc,
    operations_pb2, operations_pb2_grpc,
    instruments_pb2, instruments_pb2_grpc,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)


class ApiBroker(IBroker):
    def __init__(
            self,
            invest_api_key: str,
            account_id: str,
            instrument_id: str
        ):
        self.logger = logging.getLogger("[ApiBroker]")
        self.figi: str | None = None
        self.lot_size: int | None = None
        self.instrument_id = instrument_id
        self.account_id = account_id
        self.invest_api_key = invest_api_key
        channel = aio.secure_channel("invest-public-api.tinkoff.ru:443", ssl_channel_credentials())
        self.orders_stub = orders_pb2_grpc.OrdersServiceStub(channel)
        self.operations_stub = operations_pb2_grpc.OperationsServiceStub(channel)
        self.instruments_stub = instruments_pb2_grpc.InstrumentsServiceStub(channel)


    async def load_instrument(self):
        instrument_request = instruments_pb2.InstrumentRequest(
            id_type=instruments_pb2.InstrumentIdType.INSTRUMENT_ID_TYPE_UID,
            id=self.instrument_id,
        )
        instrument = (await
            self.instruments_stub.ShareBy(
                instrument_request,
                metadata=self._get_metadata()
            )
        ).instrument

        self.figi = instrument.figi
        self.lot_size = instrument.lot


    async def get_portfolio(self) -> GetPortfolioResponse:
        portfolio = await self.operations_stub.GetPortfolio(
            operations_pb2.PortfolioRequest(account_id=self.account_id, currency="RUB"),
            metadata=self._get_metadata()
        )

        rub_position = next(
            (pos for pos in portfolio.positions if pos.figi == "RUB000UTSTOM"),
            None
        )
        rub = ApiBroker.quotation_to_float(rub_position.quantity) if rub_position else 0.0

        instrument_position = next(
            (pos for pos in portfolio.positions if pos.figi == self.figi),
            None
        )
        shares = int(ApiBroker.quotation_to_float(instrument_position.quantity)) if instrument_position else 0

        return GetPortfolioResponse(
            rub=rub,
            shares=shares,
        )


    async def place_order(
            self,
            operation: OperationType,
            quantity: int,
            expected_price: float | None = None
    ):
        direction = orders_pb2.OrderDirection.ORDER_DIRECTION_BUY if operation == OperationType.Buy else orders_pb2.OrderDirection.ORDER_DIRECTION_SELL
        try:
            request = orders_pb2.PostOrderRequest(
                instrument_id=self.instrument_id,
                quantity=quantity,
                direction=direction,
                account_id=self.account_id,
                order_type=orders_pb2.OrderType.ORDER_TYPE_MARKET,
                order_id=str(datetime.now().timestamp())
            )

            self.logger.info(f"Place order request: {request}")

            response = await self.orders_stub.PostOrder(
                request,
                metadata=self._get_metadata()
            )

            self.logger.info(f"Place order response: {response}")

            if response.execution_report_status in [
                orders_pb2.OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL,
                orders_pb2.OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_PARTIALLYFILL
            ]:
                self.logger.info(f"Order executed: {direction} {quantity} lots")
                return
            else:
                self.logger.warning(f"Order failed: {response.message}")
                return

        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
            return False


    async def get_max_lots(self, operation: OperationType, expected_price: float | None = None) -> int:
        try:
            response = await self.orders_stub.GetMaxLots(
                orders_pb2.GetMaxLotsRequest(
                    account_id=self.account_id,
                    instrument_id=self.instrument_id
                ),
                metadata=self._get_metadata()
            )
            if operation == OperationType.Buy:
                return response.buy_limits.buy_max_lots
            else:
                return response.sell_limits.sell_max_lots

        except Exception as e:
            self.logger.error(f"Error getting max lots: {str(e)}")
            return 0

    NANO_CONVERSION_FACTOR = 10e-9
    @staticmethod
    def quotation_to_float(quotation: common_pb2.Quotation) -> float:
        return quotation.units + quotation.nano * ApiBroker.NANO_CONVERSION_FACTOR


    def _get_metadata(self):
        return [('authorization', f'Bearer {self.invest_api_key}')]
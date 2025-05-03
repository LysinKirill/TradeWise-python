import logging
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from grpc import aio
import numpy as np
import torch
import asyncio
from datetime import datetime, timezone, timedelta

from externalClients.TInvestApi.proto import (
    common_pb2,
    orders_pb2,
    orders_pb2_grpc,
    operations_pb2, operations_pb2_grpc,
    instruments_pb2, instruments_pb2_grpc,
)
from externalClients.TInvestApi.proto.marketdata_pb2 import (
    CandleInterval
)
from ml.TInvestDataProvider import TInvestDataProvider
from ml.dataAugmentation.Normalizer import Normalizer
from ml.oneMinute.LSTM.StockPriceLstm import StockPriceLstm
from ml.oneMinute.LSTM.configuration.LstmConfiguration import LstmConfiguration
from ml.runner.configuration.TradingConfiguration import TradingConfiguration


class StockTrader:
    def __init__(
            self,
            model_configuration: LstmConfiguration,  # TODO: replace with supertype for model configuration
            trading_configuration: TradingConfiguration,
            device: str,
            invest_api_key: str,
            instrument_id: str,
            account_id: str,
            figi: str,
            lot_size: int,
            channel: aio.Channel,
            buy_threshold: float = 0.001,
            sell_threshold: float = 0.003,
            lookback: int = 16,
            commission: float = 0.0005,
            request_interval: timedelta = timedelta(minutes=1),
    ):
        self.request_interval = request_interval
        self.data_provider = TInvestDataProvider(invest_api_key)
        self.logger = logging.getLogger("[STOCK_TRADER]")
        self.invest_api_key = invest_api_key
        self.device = device
        self.model = StockPriceLstm(model_configuration).to(device)
        self.trading_configuration = trading_configuration
        self.scaler: Normalizer | None = None

        self.instrument_id = instrument_id
        self.account_id = account_id
        self.figi = figi
        self.lot_size = lot_size
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.lookback = lookback
        self.commission = commission

        # gRPC stubs
        self.orders_stub = orders_pb2_grpc.OrdersServiceStub(channel)
        self.operations_stub = operations_pb2_grpc.OperationsServiceStub(channel)
        self.instruments_stub = instruments_pb2_grpc.InstrumentsServiceStub(channel)

        # State tracking
        self.current_balance: float = 0.0
        self.current_shares: int = 0
        self.price_history: list[float] = []
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model.eval().to(self.device)

        # Plotting
        self.fig, self.ax = plt.subplots(2, 1, figsize=(12, 8))
        self.price_line = None
        self.value_line = None
        self.buy_markers = []
        self.sell_markers = []
        self.plot_data = {
            'prices': [],
            'values': [],
            'buy_signals': [],
            'sell_signals': []
        }


    def load(
        self,
        saved_model_path: str,
        saved_normalizer_path: str
    ):
        self.model.load_state_dict(torch.load(saved_model_path))
        with open(saved_normalizer_path, 'rb') as f:
            params = list(map(float, f.readline().split()))
            self.scaler = Normalizer(
                min_val=params[0],
                max_val=params[1],
            )


    NANO_CONVERSION_FACTOR = 10e-9
    @staticmethod
    def quotation_to_float(quotation: common_pb2.Quotation) -> float:
        return quotation.units + quotation.nano * StockTrader.NANO_CONVERSION_FACTOR

    async def update_portfolio(self):
        """Update current balance and shares from the broker account"""
        portfolio = await self.operations_stub.GetPortfolio(
            operations_pb2.PortfolioRequest(account_id=self.account_id, currency="RUB"),
            metadata=self._get_metadata()
        )

        rub_position = next(
            (pos for pos in portfolio.positions if pos.figi == "RUB000UTSTOM"),
            None
        )
        self.current_balance = StockTrader.quotation_to_float(rub_position.quantity) if rub_position else 0.0

        instrument_position = next(
            (pos for pos in portfolio.positions if pos.figi == self.figi),
            None
        )
        self.current_shares = int(StockTrader.quotation_to_float(instrument_position.quantity)) if instrument_position else 0

    async def preload_candles(self):
        """Get the current market price for our instrument"""
        now = datetime.now(timezone.utc)
        datetime_from = now - timedelta(hours=1)
        datetime_to = now

        last_candles = await self.data_provider.get_historical_candles(
            instrument_id= self.instrument_id,
            from_time=datetime_from,
            to_time=datetime_to,
            interval=CandleInterval.CANDLE_INTERVAL_1_MIN
        )

        if len(last_candles) == 0:
            return None

        self.price_history = last_candles['close'].iloc[-(self.lookback + 1):].tolist()
        self.logger.info(f"Loaded initial price history: {self.price_history}")

    async def get_current_price(self) -> float | None:
        """Get the current market price for our instrument"""
        now = datetime.now(timezone.utc)
        datetime_from = now - timedelta(minutes=3)
        datetime_to = now

        last_candles = await self.data_provider.get_historical_candles(
            instrument_id= self.instrument_id,
            from_time=datetime_from,
            to_time=datetime_to,
            interval=CandleInterval.CANDLE_INTERVAL_1_MIN
        )

        if len(last_candles) == 0:
            return None

        return last_candles['close'].iloc[-1]


    async def place_order(
            self,
            direction: orders_pb2.OrderDirection,
            quantity: int
    ) -> bool:
        """Place an order with the broker"""
        try:
            request = orders_pb2.PostOrderRequest(
                instrument_id=self.instrument_id,
                quantity=quantity,
                direction=direction,
                account_id=self.account_id,
                order_type=orders_pb2.OrderType.ORDER_TYPE_MARKET,
                order_id=str(datetime.now().timestamp())  # Simple unique ID
            )

            response = await self.orders_stub.PostOrder(
                request,
                metadata=self._get_metadata()
            )

            if response.execution_report_status in [
                orders_pb2.OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL,
                orders_pb2.OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_PARTIALLYFILL
            ]:
                self.logger.info(f"Order executed: {direction} {quantity} lots")
                return True
            else:
                self.logger.warning(f"Order failed: {response.message}")
                return False

        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
            return False

    async def get_max_lots(self, for_buy: bool) -> int:
        """Get maximum lots we can buy/sell based on current balance/positions"""
        try:
            response = await self.orders_stub.GetMaxLots(
                orders_pb2.GetMaxLotsRequest(
                    account_id=self.account_id,
                    instrument_id=self.instrument_id
                ),
                metadata=self._get_metadata()
            )
            if for_buy:
                return response.buy_limits.buy_max_lots
            else:
                return response.sell_limits.sell_max_lots

        except Exception as e:
            self.logger.error(f"Error getting max lots: {str(e)}")
            return 0

    async def trading_cycle(self):
        """Perform one trading decision cycle"""
        self.logger.info(f"Trading cycle started. Timestamp = {datetime.now()}")
        start_time = time.monotonic()
        try:
            await self.update_portfolio()
            current_price = await self.get_current_price()
            # add current balance and price for plotting

            if current_price is None:
                self.logger.warning(f"Unable to get current price. Skipping trading cycle. timestamp={datetime.now()}")
                await asyncio.sleep(self.request_interval.seconds)
                return
            self.logger.info(f"Current price: {current_price}")
            self.price_history.append(current_price)
            self.plot_data['prices'].append(current_price)

            # Keep only recent prices for our lookback window
            if len(self.price_history) > self.lookback:
                self.price_history = self.price_history[-self.lookback:]
            else:
                self.logger.info(f"Not enough price history [{len(self.price_history)}]. Skipping trading cycle")
                return

            normalized_data = self.scaler.transform(
                np.array(self.price_history).reshape(-1, 1))
            seq = torch.FloatTensor(normalized_data).unsqueeze(0).to(self.device)

            with torch.no_grad():
                pred = self.model(seq).cpu().numpy()[0]
            pred_price = self.scaler.inverse_transform(np.array([[pred]]))[0][0]

            expected_return = (pred_price - current_price) / current_price

            max_lots = 0
            success = False

            self.logger.info(f"Current price = {current_price}, Predicted price = {pred_price}, expected return = {expected_return}")
            if expected_return > self.buy_threshold and self.current_shares == 0:
                max_lots = await self.get_max_lots(for_buy=True)
            if max_lots > 0:
                self.logger.info(f"Place buy order for {max_lots} lots")
                success = await self.place_order(
                    direction=orders_pb2.OrderDirection.ORDER_DIRECTION_BUY,
                    quantity=max_lots
                )
            if success:
                self.plot_data['buy_signals'].append(
                    (len(self.plot_data['prices']) - 1, current_price))
            elif expected_return < -self.sell_threshold and self.current_shares > 0:
                max_lots = await self.get_max_lots(for_buy=False)
                if max_lots > 0:
                    self.logger.info(f"Place sell order for {max_lots} lots")
                    success = await self.place_order(
                        direction=orders_pb2.OrderDirection.ORDER_DIRECTION_SELL,
                        quantity=max_lots
                    )
            if success:
                self.plot_data['sell_signals'].append(
                    (len(self.plot_data['prices']) - 1, current_price))

            position_value = self.current_shares * current_price
            total_value = self.current_balance + position_value
            self.plot_data['values'].append(total_value)

            self.update_plot()

        except Exception as e:
            self.logger.error(f"Error in trading cycle: {str(e)}")
        finally:
            cycle_duration = time.monotonic() - start_time
            if cycle_duration < self.request_interval.seconds:
                await asyncio.sleep(self.request_interval.seconds - cycle_duration)


    async def start_trading(self):
        """Start the continuous trading loop"""
        self.logger.info("Starting trading bot...")
        await self.preload_candles()
        while True:
            try:
                await self.trading_cycle()
            except KeyboardInterrupt:
                self.logger.info("\nGracefully shutting down trading bot...")
                break
            except asyncio.CancelledError:
                self.logger.info("Trading bot stopped")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                await asyncio.sleep(60)

    def _get_metadata(self):
        return [('authorization', f'Bearer {self.invest_api_key}')]

    def init_plot(self):
        """Initialize the plot"""
        plt.ion()  # Interactive mode
        self.fig.suptitle(f"Live Trading: {self.instrument_id}")

        # Price plot
        self.ax[0].set_title('Price with Signals')
        self.ax[0].set_ylabel('Price')
        self.price_line, = self.ax[0].plot([], [], 'b-', label='Price')
        self.ax[0].legend()

        # Portfolio value plot
        self.ax[1].set_title('Portfolio Value')
        self.ax[1].set_ylabel('Value')
        self.ax[1].set_xlabel('Time')
        self.value_line, = self.ax[1].plot([], [], 'g-', label='Portfolio Value')
        self.ax[1].legend()

        plt.tight_layout()

    def update_plot(self):
        """Update the plot with new data"""
        if not self.plot_data['prices']:
            return

        # Update price plot
        x = range(len(self.plot_data['prices']))
        self.price_line.set_data(x, self.plot_data['prices'])
        self.ax[0].relim()
        self.ax[0].autoscale_view()

        # Update markers
        for marker in self.buy_markers + self.sell_markers:
            marker.remove()
        self.buy_markers = []
        self.sell_markers = []

        if self.plot_data['buy_signals']:
            bx, by = zip(*self.plot_data['buy_signals'])
            self.buy_markers = self.ax[0].scatter(
                bx, by, color='green', marker='^', s=100, label='Buy')

        if self.plot_data['sell_signals']:
            sx, sy = zip(*self.plot_data['sell_signals'])
            self.sell_markers = self.ax[0].scatter(
                sx, sy, color='red', marker='v', s=100, label='Sell')

        # Update value plot
        if self.plot_data['values']:
            self.value_line.set_data(x[-len(self.plot_data['values']):], self.plot_data['values'])
            self.ax[1].relim()
            self.ax[1].autoscale_view()

        plt.draw()
        plt.pause(0.01)
import logging
from collections.abc import AsyncGenerator

import numpy as np
import torch
import asyncio
import traceback
from app.domain.models.invest.CandleModel import CandleModel
from ml.data.interface.IBroker import IBroker
from ml.data.interface.ICandleGenerator import ICandleGenerator
from ml.data.interface.ITradingWindowManager import ITradingWindowManager
from ml.data.model.OperationType import OperationType
from ml.dataAugmentation.Normalizer import Normalizer
from ml.oneMinute.LSTM.StockPriceLstm import StockPriceLstm
from ml.oneMinute.LSTM.configuration.LstmConfiguration import LstmConfiguration
from ml.runner.configuration.TradingConfiguration import TradingConfiguration


class PerfectStockTrader:
    def __init__(
            self,
            model_configuration: LstmConfiguration,  # TODO: replace with supertype for model configuration
            trading_configuration: TradingConfiguration,
            candle_source: ICandleGenerator,
            broker: IBroker,
            trading_window_manager: ITradingWindowManager,
            device: str,
            invest_api_key: str,
            instrument_id: str,
            lookback: int = 16,
            commission: float = 0.0005,
            log_file: str = "../logging/stock_trader.log"
    ):
        self.last_buy_price: float | None = None
        self.trading_window_manager = trading_window_manager
        self.broker = broker
        self.candle_source = candle_source
        self.logger = logging.getLogger("[STOCK_TRADER]")

        self.logger.handlers = []

        # Disable propagation to root logger (stops double logging)
        self.logger.propagate = False
        # if self.logger.hasHandlers():
        #     self.logger.handlers.clear()
        file_handler = logging.FileHandler(log_file, mode="w")
        self.logger.addHandler(file_handler)

        self.invest_api_key = invest_api_key
        self.device = device
        self.model = StockPriceLstm(model_configuration).to(device)
        self.trading_configuration = trading_configuration

        self.instrument_id = instrument_id
        self.lookback = lookback
        self.commission = commission

        # State tracking
        self.current_balance: float = 0.0
        self.current_shares: int = 0
        self.price_history: list[float] = []
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model.eval().to(self.device)
        self.scaler: Normalizer | None = None
        self.current_candle = 1
        self.iterations = 0

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


    async def trading_cycle(self, current_candle: CandleModel, next_candle: CandleModel):
        """Perform one trading decision cycle"""
        #self.logger.info(f"Trading cycle started. Timestamp = {datetime.now()}")
        try:
            await self.broker.load_instrument()
            portfolio_result = await self.broker.get_portfolio()
            if portfolio_result is not None:
                self.current_balance = portfolio_result.rub
                self.current_shares = portfolio_result.shares

            current_price = current_candle.close

            self.price_history.append(current_price)

            # Keep only recent prices for our lookback window
            if len(self.price_history) > self.lookback:
                self.price_history = self.price_history[-self.lookback:]
            else:
                self.logger.info(f"Not enough price history [{len(self.price_history)}]. Skipping trading cycle")
                return

            normalized_data = self.scaler.transform(
                np.array(self.price_history).reshape(-1, 1))
            seq = torch.FloatTensor(normalized_data).unsqueeze(0).to(self.device)

            # with torch.no_grad():
                # pred = self.model(seq).cpu().numpy()[0]
                #pred_price = self.scaler.inverse_transform(np.array([[pred]]))[0][0]

            #uniform_random = np.random.uniform(low=-0.001, high=0.001)
            #normal_random = np.random.normal(loc=0.001, scale=0.001 / 3)

            #pred_price = next_candle.close * (1 + float(normal_random))
            pred_price = next_candle.close

            expected_return = (pred_price - current_price) / current_price
            trade_available = await self.trading_window_manager.check_trade_available(
                instrument_id=self.instrument_id,
                timestamp=current_candle.timestamp,
            )
            #self.logger.info(f"Candle #{self.current_candle}: Current price = {current_price:.3f}, Predicted price = {pred_price:.3f}, expected return = {expected_return:.5f}.  DATA: {self.scaler.transform(
            #    np.array(self.price_history).reshape(-1, 1))}")
            self.logger.info(f"Candle #{self.current_candle}: Current price = {current_price:.3f}, Predicted price = {pred_price:.3f}, expected return = {expected_return:.5f}. Portfolio value = {await self.broker.get_portfolio_value(current_price):.2f}, Timestamp = {current_candle.timestamp}" + ("" if trade_available else " [Trade unavailable]"))
            self.current_candle += 1

            if not trade_available:
                return



            if expected_return > self.trading_configuration.buy_signal and self.current_shares == 0:
                max_lots = await self.broker.get_max_lots(OperationType.Buy, expected_price=current_price)
                if max_lots > 0:
                    self.logger.info(f"Place buy order for {max_lots} lots")
                    await self.broker.place_order(
                        operation=OperationType.Buy,
                        quantity=max_lots,
                        expected_price=current_price,
                    )
                    self.last_buy_price = current_price
            elif expected_return < -self.trading_configuration.sell_signal and self.current_shares > 0:
                max_lots = await self.broker.get_max_lots(OperationType.Sell, expected_price=current_price)
                if max_lots > 0:
                    self.logger.info(f"Place sell order for {max_lots} lots")
                    await self.broker.place_order(
                        OperationType.Sell,
                        quantity=max_lots,
                        expected_price=current_price
                    )

            price_change_since_last_buy = (current_price - self.last_buy_price) / self.last_buy_price if self.last_buy_price is not None else None
            if price_change_since_last_buy is not None and self.current_shares != 0:
                if (
                        self.trading_configuration.stop_loss is not None and
                        price_change_since_last_buy < -self.trading_configuration.stop_loss
                ) or (
                        self.trading_configuration.take_profit is not None and
                        price_change_since_last_buy > self.trading_configuration.take_profit
                ):
                    max_lots = await self.broker.get_max_lots(OperationType.Sell, expected_price=current_price)
                    #max_lots = 0
                    if max_lots > 0:
                        is_take_profit = self.trading_configuration.take_profit is not None and price_change_since_last_buy > self.trading_configuration.take_profit
                        self.logger.warning(f"Portfolio value before take_profit/stop_loss: {await self.broker.get_portfolio_value(current_price)}")
                        self.logger.warning(f"{'[TAKE_PROFIT]' if is_take_profit else '[STOP_LOSS]'} Place sell order for {max_lots} lots. Estimated loss/profit = {price_change_since_last_buy * self.current_shares * self.last_buy_price}; {price_change_since_last_buy = }, {self.current_shares = }, {self.last_buy_price = }")
                        await self.broker.place_order(
                            OperationType.Sell,
                            quantity=max_lots,
                            expected_price=current_price
                        )
                        self.logger.warning(f"Portfolio value after take_profit/stop_loss: {await self.broker.get_portfolio_value(current_price)}")



        except Exception as e:
            self.logger.error(f"Error in trading cycle: {str(e)}")
            traceback.print_exc()

    @staticmethod
    async def anext_or_none(generator: AsyncGenerator):
        try:
            return await anext(generator)
        except StopAsyncIteration:
            return None

    async def start_trading(self):
        """Start the continuous trading loop"""
        self.logger.info("Starting trading bot...")
        self.iterations = 0
        next_candle_generator = self.candle_source.generate_candles(
            self.instrument_id,
            preload_candles_count=self.lookback
        )
        await anext(next_candle_generator)
        async for candle in self.candle_source.generate_candles(self.instrument_id, preload_candles_count=self.lookback):
            try:
                next_candle = await PerfectStockTrader.anext_or_none(next_candle_generator)
                if next_candle is None:
                    next_candle = candle

                self.iterations += 1
                if candle is None:
                    self.logger.warning("Received no candle from candle source! Skipping trading cycle. timestamp={datetime.now()}")
                    continue

                await self.trading_cycle(candle, next_candle)
            except KeyboardInterrupt:
                self.logger.info("\nGracefully shutting down trading bot...")
                break
            except asyncio.CancelledError:
                self.logger.info("Trading bot stopped")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                await asyncio.sleep(60)

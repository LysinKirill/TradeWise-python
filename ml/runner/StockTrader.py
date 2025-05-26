import asyncio
import logging
import traceback
import numpy as np
import torch
from app.domain.models.invest.CandleModel import CandleModel
from ml.data.interface.IBroker import IBroker
from ml.data.interface.ICandleGenerator import ICandleGenerator
from ml.data.interface.ITradingWindowManager import ITradingWindowManager
from ml.data.model.OperationType import OperationType
from ml.dataAugmentation.Normalizer import Normalizer
from ml.runner.configuration.TradingConfiguration import TradingConfiguration


class StockTrader:
    def __init__(
            self,
            model: torch.nn.Module,
            scaler: Normalizer,
            trading_configuration: TradingConfiguration,
            candle_source: ICandleGenerator,
            broker: IBroker,
            trading_window_manager: ITradingWindowManager,
            invest_api_key: str,
            account_id: str,
            instrument_id: str,
            lookback: int = 16,
            commission: float = 0.0005
    ):

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.ERROR)
        self.logger = logger
        self.last_buy_price: float | None = None
        self.trading_window_manager = trading_window_manager
        self.broker = broker
        self.candle_source = candle_source

        self.invest_api_key = invest_api_key
        self.account_id = account_id
        self.model = model
        self.trading_configuration = trading_configuration

        self.instrument_id = instrument_id
        self.lookback = lookback
        self.commission = commission

        self.current_balance: float = 0.0
        self.current_shares: int = 0
        self.candle_history: list[CandleModel] = []
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model.eval().to(self.device)
        self.scaler = scaler
        self.current_candle = 1
        self.iterations = 0


    async def trading_cycle(self, current_candle: CandleModel):
        try:
            await self.broker.load_instrument(self.instrument_id, self.invest_api_key)
            portfolio_result = await self.broker.get_portfolio(self.invest_api_key, self.account_id, self.instrument_id)
            if portfolio_result is not None:
                self.current_balance = portfolio_result.rub
                self.current_shares = portfolio_result.shares

            current_price = current_candle.close

            self.candle_history.append(current_candle)

            if len(self.candle_history) > self.lookback:
                self.candle_history = self.candle_history[-self.lookback:]
            else:
                self.logger.info(f"Not enough price history [{len(self.candle_history)}]. Skipping trading cycle")
                return

            features = np.array([
                [candle.close]
                for candle in self.candle_history
            ])

            normalized_data = self.scaler.transform(features)
            seq = torch.FloatTensor(normalized_data).unsqueeze(0).to(self.device)

            with torch.no_grad():
                pred = self.model(seq).cpu().numpy()[0]
                pred_price = self.scaler.inverse_transform(
                    np.array([[pred, pred, pred, pred, 0]])
                )[0][3]

            expected_return = (pred_price - current_price) / current_price
            trade_available = await self.trading_window_manager.check_trade_available(
                instrument_id=self.instrument_id,
                timestamp=current_candle.timestamp,
            )

            portfolio_value = await self.broker.get_portfolio_value(current_price)

            self.logger.info(
                f"Candle #{self.current_candle}:"
                f" Current price = {current_price:.3f},"
                f" Predicted price = {pred_price:.3f},"
                f" expected return = {expected_return:.5f}."
                f" Portfolio value = {portfolio_value:.2f},"
                f" Timestamp = {current_candle.timestamp}" + ("" if trade_available else " [Trade unavailable]")
            )
            self.current_candle += 1

            if not trade_available:
                return

            if expected_return > self.trading_configuration.buy_signal and self.current_shares == 0:
                max_lots = await self.broker.get_max_lots(
                    invest_api_key=self.invest_api_key,
                    account_id=self.account_id,
                    instrument_id=self.instrument_id,
                    operation=OperationType.Buy,
                    expected_price=current_price
                )
                if max_lots > 0:
                    self.logger.info(f"Place buy order for {max_lots} lots")
                    await self.broker.place_order(
                        invest_api_key=self.invest_api_key,
                        account_id=self.account_id,
                        instrument_id=self.instrument_id,
                        operation=OperationType.Buy,
                        quantity=max_lots,
                        expected_price=current_price,
                    )

                    self.last_buy_price = current_price
            elif expected_return < -self.trading_configuration.sell_signal and self.current_shares > 0:
                max_lots = await self.broker.get_max_lots(
                    invest_api_key=self.invest_api_key,
                    instrument_id=self.instrument_id,
                    account_id=self.account_id,
                    operation=OperationType.Sell,
                    expected_price=current_price
                )

                if max_lots > 0:
                    self.logger.info(f"Place sell order for {max_lots} lots")
                    await self.broker.place_order(
                        invest_api_key=self.invest_api_key,
                        instrument_id=self.instrument_id,
                        account_id=self.account_id,
                        operation=OperationType.Sell,
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
                    max_lots = await self.broker.get_max_lots(
                        invest_api_key=self.invest_api_key,
                        account_id=self.account_id,
                        instrument_id=self.instrument_id,
                        operation=OperationType.Sell,
                        expected_price=current_price
                    )
                    if max_lots > 0:
                        is_take_profit = self.trading_configuration.take_profit is not None and price_change_since_last_buy > self.trading_configuration.take_profit
                        self.logger.warning(f"Portfolio value before take_profit/stop_loss: {await self.broker.get_portfolio_value(current_price)}")
                        self.logger.warning(f"{'[TAKE_PROFIT]' if is_take_profit else '[STOP_LOSS]'} Place sell order for {max_lots} lots. Estimated loss/profit = {price_change_since_last_buy * self.current_shares * self.last_buy_price}; {price_change_since_last_buy = }, {self.current_shares = }, {self.last_buy_price = }")
                        await self.broker.place_order(
                            invest_api_key=self.invest_api_key,
                            instrument_id=self.instrument_id,
                            account_id=self.account_id,
                            operation=OperationType.Sell,
                            quantity=max_lots,
                            expected_price=current_price
                        )
                        self.logger.warning(f"Portfolio value after take_profit/stop_loss: {await self.broker.get_portfolio_value(current_price)}")

        except Exception as e:
            self.logger.error(f"Error in trading cycle: {str(e)}")
            traceback.print_exc()


    async def start_trading(self):
        """Start the continuous trading loop"""
        self.logger.info("Starting trading bot...")
        self.iterations = 0
        async for candle in self.candle_source.generate_candles(self.instrument_id, preload_candles_count=self.lookback):
            try:
                self.iterations += 1
                if candle is None:
                    self.logger.warning("Received no candle from candle source! Skipping trading cycle. timestamp={datetime.now()}")
                    continue

                await self.trading_cycle(candle)
            except KeyboardInterrupt:
                self.logger.info("\nGracefully shutting down trading bot...")
                break
            except asyncio.CancelledError:
                self.logger.info("Trading bot stopped")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                raise
                #await asyncio.sleep(60)

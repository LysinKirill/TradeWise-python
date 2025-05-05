from datetime import datetime, time

from ml.data.interface.ITradingWindowManager import ITradingWindowManager


class PresetTradingWindowManager(ITradingWindowManager):
    def __init__(
            self,
            trading_windows: list[tuple[time, time]]
    ):
        self.trading_windows = trading_windows

    async def check_trade_available(self, instrument_id: str, timestamp: datetime):
        return any(
            trading_window[0] <= timestamp.time() <= trading_window[1] for trading_window in self.trading_windows)
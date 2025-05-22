from datetime import datetime

from ml.data.interface.ITradingWindowManager import ITradingWindowManager


class ConstantTradingWindowManager(ITradingWindowManager):
    def __init__(self, constant_trading_flag: bool):
        self.trading_flag = constant_trading_flag


    async def check_trade_available(self, instrument_id: str, timestamp: datetime):
        return self.trading_flag
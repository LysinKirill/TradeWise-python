from ml.data.interface.IBroker import IBroker
from ml.data.model.OperationType import OperationType
from ml.data.model.responses.GetPortfolioResponse import GetPortfolioResponse


class TestBroker(IBroker):
    def __init__(
            self,
            start_balance: float,
            lot_size: int,
            commission: float,
    ):
        self.balance = start_balance
        self.shares = 0
        self.lot_size = lot_size
        self.commission = commission
        self.total_trades = 0
        self.portfolio_value = start_balance


    async def load_instrument(self):
        pass

    async def get_portfolio(self) -> GetPortfolioResponse:
        return GetPortfolioResponse(self.balance, self.shares)

    async def place_order(self, operation: OperationType, quantity: int, expected_price: float | None = None):
        self.total_trades += 1
        if operation == OperationType.Buy:
            self.shares = quantity * self.lot_size
            commission_paid = self.shares * (expected_price * self.commission)
            self.balance = self.balance - (self.shares * expected_price + commission_paid)
        else:
            commission_paid = self.shares * (expected_price * self.commission)
            self.balance = self.balance + (self.shares * expected_price - commission_paid)
            self.shares = 0

        self.portfolio_value = self.balance + self.shares * (expected_price * (1 - self.commission))


    async def get_max_lots(self, operation: OperationType, expected_price: float | None = None) -> int:
        if operation == OperationType.Buy:
            return int(self.balance // (expected_price * self.lot_size * (1 + self.commission)))

        return self.shares // self.lot_size
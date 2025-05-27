from app.domain.models.user.UserAssetInfoModel import UserAssetInfoModel
from app.domain.services.IClaimValuesService import IClaimValuesService
from dataAccess.interfaces.IUserRepository import IUserRepository
from externalClients.TInvestApi.const.Instruments import Instrument
from app.domain.models.user.responses.GetPortfolioResponseModel import GetPortfolioResponseModel
from externalClients.TInvestApi.handlers.BaseClient import BaseClient
from externalClients.TInvestApi.proto import (
    operations_pb2, operations_pb2_grpc,
)

class OperationClient(BaseClient):
    def __init__(
            self,
            endpoint: str,
            claim_values_service: IClaimValuesService,
            user_repository: IUserRepository
    ):
        super().__init__(endpoint, claim_values_service, user_repository)
        self.stub = operations_pb2_grpc.OperationsServiceStub(self.channel)

    async def get_portfolio(self, account_id: str) -> GetPortfolioResponseModel | None:
        request = operations_pb2.PortfolioRequest(account_id=account_id)
        response = await self.stub.GetPortfolio(request, metadata=await self.get_metadata())

        ruble_balance = None
        asset_positions = []

        for position in response.positions:
            if position.instrument_uid == Instrument.RUB:
                ruble_balance = position.quantity.units
                continue

            asset_positions.append(
                UserAssetInfoModel(
                    instrument_id=position.instrument_uid,
                    quantity=position.quantity.units,
                    ticker=position.ticker,
                    daily_yield=BaseClient._money_to_float(position.daily_yield),
                    current_price=BaseClient._money_to_float(position.current_price),
                )
            )

        if ruble_balance is None:
            return None

        return GetPortfolioResponseModel(
            ruble_balance=ruble_balance,
            positions=asset_positions
        )

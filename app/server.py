import asyncio

import grpc
from grpc import aio
import os
from dotenv import load_dotenv
from dependency_injector import containers, providers
import logging
import sys

from app.configuration import Settings, SupportedInstrumentsOptions
from app.grpcServices.InvestGrpcService import InvestGrpcService
from app.grpcServices.ModelGrpcService import ModelGrpcService
from app.grpcServices.BacktestGrpcService import BacktestGrpcService
from app.interceptors.ContextInterceptor import ContextInterceptor
from app.proto import (
    user_pb2_grpc,
    invest_pb2_grpc,
    model_pb2_grpc,
    backtest_pb2_grpc
)

from app.grpcServices.UserGrpcService import UserGrpcService
from app.services.InvestService import InvestService
from app.services.ModelExecutionService import ModelExecutionService
from app.services.ModelService import ModelService
from app.services.UserService import UserService
from app.services.ClaimValuesService import ClaimValuesService
from app.infrastructure.GrpcContextAccessor import GrpcContextAccessor
from app.workers.ModelExecutionWorker import ModelExecutionWorker
from dataAccess.ExecutionRepository import ExecutionRepository
from dataAccess.UserRepository import UserRepository
from dataAccess.PgModelRepository import PgModelRepository
from dataAccess.PgConnectionProvider import PgConnectionProvider
from externalClients.TInvestApi.handlers.MarketDataClient import MarketDataClient
from externalClients.TInvestApi.handlers.InstrumentsClient import InstrumentsClient
from externalClients.TInvestApi.handlers.OperationsClient import OperationClient
from externalClients.TInvestApi.handlers.UserClient import UserClient
from ml.data.ApiBroker import ApiBroker
from ml.data.ApiCandleGenerator import ApiCandleGenerator
from ml.data.ConstantTradingWindowManager import ConstantTradingWindowManager
from ml.data.RetryPolicy import RetryPolicy
from ml.data.configuration.BackoffStrategy import BackoffStrategy
from ml.data.configuration.RetryPolicyConfiguration import RetryPolicyConfiguration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

SECONDS_IN_MINUTE = 60
GRACE_PERIOD_IN_SECOND = 15
SERVER_PORT = 50051

TINKOFF_API_PROD = 'invest-public-api.tinkoff.ru:443'
TINKOFF_API_SANDBOX = 'sandbox-invest-public-api.tinkoff.ru:443'



class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    settings = providers.Singleton(Settings.Settings)

    supported_instruments_options = providers.Factory(
        SupportedInstrumentsOptions.SupportedInstrumentsOptions,
        settings = settings
    )

    retry_policy_configuration = RetryPolicyConfiguration(
        initial_delay_in_seconds=5,
        allowed_attempts=3,
        backoff_strategy=BackoffStrategy.Linear
    )

    t_api_token = config.INVEST_TOKEN
    t_api_endpoint = config.TINKOFF_API_PROD
    jwt_secret = config.JWT_SECRET

    context_accessor = providers.Singleton(GrpcContextAccessor)
    claim_values_service = providers.Singleton(
        ClaimValuesService,
        context_accessor=context_accessor,
        jwt_secret=jwt_secret,
    )

    pg_connection_provider = providers.Singleton(
        PgConnectionProvider,
        username=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        host=os.getenv('DB_HOST','python-db'),
        port=int(os.getenv('DB_PORT', 5432)),
        db=os.getenv('DB_NAME', 'python-db')
    )

    user_repository = providers.Factory(
        UserRepository,
        connection_provider=pg_connection_provider
    )

    model_repository = providers.Factory(
        PgModelRepository,
        connection_provider=pg_connection_provider
    )

    execution_repository = providers.Factory(
        ExecutionRepository,
        connection_provider=pg_connection_provider
    )

    user_client = providers.Singleton(
        UserClient,
        endpoint=t_api_endpoint,
        api_key=t_api_token
    )
    instruments_client = providers.Singleton(
        InstrumentsClient,
        endpoint=t_api_endpoint,
        api_key=t_api_token
    )
    marketdata_client = providers.Singleton(
        MarketDataClient,
        endpoint=t_api_endpoint,
        api_key=t_api_token
    )
    operations_client = providers.Singleton(
        OperationClient,
        endpoint=t_api_endpoint,
        api_key=t_api_token
    )
    user_service = providers.Factory(
        UserService,
        user_client=user_client,
        operations_client=operations_client,
        user_repository=user_repository
    )
    invest_service = providers.Factory(
        InvestService,
        instruments_client=instruments_client,
        marketdata_client=marketdata_client,
        supported_instruments_options=supported_instruments_options,
    )
    model_service = providers.Factory(
        ModelService,
        model_repository=model_repository,
    )
    candle_generator_factory = providers.Singleton(
        ApiCandleGenerator,
        marketdata_client=marketdata_client,
        fetch_delay_in_seconds=SECONDS_IN_MINUTE,
        retry_policy=RetryPolicy(retry_policy_configuration)
    )
    broker = providers.Singleton(
        ApiBroker
    )

    # trading_window_manager = PresetTradingWindowManager(
    #     trading_windows=[(time(hour=7, minute=0, second=0, microsecond=0),
    #                       time(hour=16, minute=50, second=0, microsecond=0))],
    # )

    trading_window_manager = providers.Singleton(
        ConstantTradingWindowManager,
        constant_trading_flag=True
    )

    model_execution_service = providers.Factory(
        ModelExecutionService,
        model_repository=model_repository,
        execution_repository=execution_repository,
        user_service=user_service,
        candle_generator_factory=candle_generator_factory,
        broker=broker,
        trading_window_manager=trading_window_manager,
    )
    user_grpc_service = providers.Factory(
        UserGrpcService,
        user_service=user_service,
        claim_values_service=claim_values_service
    )
    invest_grpc_service = providers.Factory(
        InvestGrpcService,
        invest_service=invest_service,
        claim_values_service=claim_values_service
    )
    model_grpc_service = providers.Factory(
        ModelGrpcService,
        model_service=model_service,
        model_execution_service=model_execution_service,
        claim_values_service=claim_values_service
    )
    backtest_grpc_service = providers.Factory(
        BacktestGrpcService
    )

    model_execution_worker = providers.Factory(
        ModelExecutionWorker,
        execution_service=model_execution_service,
        interval_seconds=60
    )


async def serve():
    load_dotenv()

    access_token = os.environ.get("INVEST_TOKEN")
    jwt_secret = os.environ.get("JWT_SECRET")
    if not access_token:
        raise ValueError("Environment variable INVEST_TOKEN is not set!")
    if not jwt_secret:
        raise ValueError("Environment variable JWT_SECRET is not set!")

    container = Container()
    container.config.override({
        'INVEST_TOKEN': access_token,
        'TINKOFF_API_PROD': TINKOFF_API_PROD,
        'JWT_SECRET': jwt_secret,
    })

    context_interceptor = ContextInterceptor(container.context_accessor())

    server = aio.server(
        interceptors=(context_interceptor,)
    )

    register_grpc_services(container, server)

    try:
        with open('./certs/cert.pem', 'rb') as f:
            cert = f.read()
        with open('./certs/key.pem', 'rb') as f:
            key = f.read()

        server_credentials = grpc.ssl_server_credentials(
            [(key, cert)]
        )

        server.add_secure_port(f'[::]:{SERVER_PORT}', server_credentials)
        logger.info(f"Server started on [::]:{SERVER_PORT}")

    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise

    await server.start()
    logger.info("Server is running...")

    worker = container.model_execution_worker()
    worker_task = asyncio.create_task(worker.start())

    try:
        while True:
            await asyncio.sleep(1)
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Shutdown signal received. Gracefully stopping server...")
        await worker.stop()
        await worker_task
        await server.stop(GRACE_PERIOD_IN_SECOND)


def register_grpc_services(container: Container, server: grpc.Server):
    user_grpc_service = container.user_grpc_service()
    user_pb2_grpc.add_UserServiceServicer_to_server(user_grpc_service, server)

    invest_grpc_service = container.invest_grpc_service()
    invest_pb2_grpc.add_InvestServiceServicer_to_server(invest_grpc_service, server)

    model_grpc_service = container.model_grpc_service()
    model_pb2_grpc.add_ModelServiceServicer_to_server(model_grpc_service, server)

    backtest_grpc_service = container.backtest_grpc_service()
    backtest_pb2_grpc.add_BacktestServiceServicer_to_server(backtest_grpc_service, server)


if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if 'pydevd' in sys.modules:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(serve())
        finally:
            loop.close()
    else:
        asyncio.run(serve())
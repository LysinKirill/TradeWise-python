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
from app.interceptors.ContextInterceptor import ContextInterceptor
from app.proto import (
    user_pb2_grpc,
    invest_pb2_grpc,
    model_pb2_grpc,
)

from app.grpcServices.UserGrpcService import UserGrpcService
from app.services.InvestService import InvestService
from app.services.ModelService import ModelService
from app.services.UserService import UserService
from app.services.ClaimValuesService import ClaimValuesService
from app.infrastructure.GrpcContextAccessor import GrpcContextAccessor
from dataAccess.LocalModelRepository import LocalModelRepository
from dataAccess.UserRepository import UserRepository
from dataAccess.PgModelRepository import PgModelRepository
from dataAccess.PgConnectionProvider import PgConnectionProvider
from externalClients.TInvestApi.handlers.MarketDataClient import MarketDataClient
from externalClients.TInvestApi.handlers.InstrumentsClient import InstrumentsClient
from externalClients.TInvestApi.handlers.UserClient import UserClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

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

    fallback_model_repository = providers.Factory(
        LocalModelRepository,
        base_dir="./ml/savedModels"
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
    user_service = providers.Factory(
        UserService,
        user_client=user_client,
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
        fallback_model_repository=fallback_model_repository,
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
        claim_values_service=claim_values_service
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

    try:
        while True:
            await asyncio.sleep(1)
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Shutdown signal received. Gracefully stopping server...")
        await server.stop(GRACE_PERIOD_IN_SECOND)


def register_grpc_services(container: Container, server: grpc.Server):
    user_grpc_service = container.user_grpc_service()
    user_pb2_grpc.add_UserServiceServicer_to_server(user_grpc_service, server)

    invest_grpc_service = container.invest_grpc_service()
    invest_pb2_grpc.add_InvestServiceServicer_to_server(invest_grpc_service, server)

    model_grpc_service = container.model_grpc_service()
    model_pb2_grpc.add_ModelServiceServicer_to_server(model_grpc_service, server)


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
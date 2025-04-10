import grpc
from concurrent import futures
import time
import os
from dotenv import load_dotenv
from dependency_injector import containers, providers
import logging
import sys


from app.grpcServices.InvestGrpcService import InvestGrpcService
from app.interceptors.ContextInterceptor import ContextInterceptor
from app.proto import (
    hello_pb2_grpc,
    user_pb2_grpc,
    invest_pb2_grpc
)
from app.grpcServices.HelloGrpcService import HelloGrpcService
from app.grpcServices.UserGrpcService import UserGrpcService
from app.services.HelloService import HelloService
from app.services.InvestService import InvestService
from app.services.UserService import UserService
from app.services.ClaimValuesService import ClaimValuesService
from app.infrastructure.GrpcContextAccessor import GrpcContextAccessor
from dataAccess.UserRepository import UserRepository
from dataAccess.PgConnectionProvider import PgConnectionProvider
from externalClients.TInvestApi.handlers.InstrumentsClient import InstrumentsClient
from externalClients.TInvestApi.handlers.UserClient import UserClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

SECONDS_IN_DAY = 86400
SERVER_PORT = 50051

TINKOFF_API_PROD = 'invest-public-api.tinkoff.ru:443'
TINKOFF_API_SANDBOX = 'sandbox-invest-public-api.tinkoff.ru:443'



class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

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
        username='postgres',
        password='postgres',
        host='python-db',
        port=5432,
        db='python-db'
    )

    user_repository = providers.Factory(
        UserRepository,
        connection_provider=pg_connection_provider
    )

    hello_service = providers.Singleton(HelloService)
    hello_grpc_service = providers.Factory(
        HelloGrpcService,
        hello_service=hello_service
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
    user_service = providers.Factory(
        UserService,
        user_client=user_client,
        user_repository=user_repository
    )
    invest_service = providers.Factory(
        InvestService,
        instruments_client=instruments_client,
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


def serve():
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

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
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
        logger.info(f"Failed to start server: {str(e)}")
        raise

    server.start()
    try:
        while True:
            time.sleep(SECONDS_IN_DAY)
    except KeyboardInterrupt:
        logger.info("Stopping server...")
        server.stop(0)


def register_grpc_services(container: Container, server: grpc.Server):
    hello_grpc_service = container.hello_grpc_service()
    hello_pb2_grpc.add_HelloWorldServicer_to_server(hello_grpc_service, server)
    user_grpc_service = container.user_grpc_service()
    user_pb2_grpc.add_UserServiceServicer_to_server(user_grpc_service, server)
    invest_grpc_service = container.invest_grpc_service()
    invest_pb2_grpc.add_InvestServiceServicer_to_server(invest_grpc_service, server)


if __name__ == '__main__':
    serve()
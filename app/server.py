import grpc
from concurrent import futures
import time
import os
from dotenv import load_dotenv
from dependency_injector import containers, providers

from app.proto import (
    hello_pb2_grpc,
    user_pb2_grpc
)
from app.grpcServices.HelloGrpcService import HelloGrpcService
from app.grpcServices.UserGrpcService import UserGrpcService
from app.services.HelloService import HelloService
from app.services.UserService import UserService
from externalClients.TInvestApi.handlers.UserClient import UserClient


SECONDS_IN_DAY = 86400
SERVER_HOST = 'localhost'
SERVER_PORT = 50051

TINKOFF_API_PROD = 'invest-public-api.tinkoff.ru:443'
TINKOFF_API_SANDBOX = 'sandbox-invest-public-api.tinkoff.ru:443'


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    t_api_token = config.INVEST_TOKEN
    t_api_endpoint = config.TINKOFF_API_PROD

    hello_service = providers.Singleton(HelloService)
    hello_grpc_service = providers.Factory(
        HelloGrpcService,
        hello_service=hello_service
    )

    user_client = providers.Singleton(
        UserClient,
        endpoint=t_api_endpoint,
        token=t_api_token
    )
    user_service = providers.Factory(
        UserService,
        user_client=user_client
    )
    user_grpc_service = providers.Factory(
        UserGrpcService,
        user_service=user_service
    )




def serve():
    load_dotenv()

    access_token = os.environ.get("INVEST_TOKEN")
    if not access_token:
        raise ValueError("Environment variable INVEST_TOKEN is not set!")

    container = Container()
    container.config.override({
        'INVEST_TOKEN': access_token,
        'TINKOFF_API_PROD': TINKOFF_API_PROD
    })

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    register_grpc_services(container, server)

    server.add_insecure_port(f'{SERVER_HOST}:{SERVER_PORT}')
    print(f"Starting server on {SERVER_HOST}:{SERVER_PORT}")

    server.start()
    try:
        while True:
            time.sleep(SECONDS_IN_DAY)
    except KeyboardInterrupt:
        print("Stopping server...")
        server.stop(0)


def register_grpc_services(container: Container, server: grpc.Server):
    hello_grpc_service = container.hello_grpc_service()
    hello_pb2_grpc.add_HelloWorldServicer_to_server(hello_grpc_service, server)
    user_grpc_service = container.user_grpc_service()
    user_pb2_grpc.add_UserServiceServicer_to_server(user_grpc_service, server)


if __name__ == '__main__':
    serve()
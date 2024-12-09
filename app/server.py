import grpc
from concurrent import futures
import time
from app.proto import hello_pb2_grpc
from app.grpcServices.HelloGrpcService import HelloGrpcService
from app.services.HelloService import HelloService
from dependency_injector import containers, providers

SECONDS_IN_DAY = 86400
SERVER_HOST = 'localhost'
SERVER_PORT = 50051


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    hello_service = providers.Singleton(HelloService)
    hello_grpc_service = providers.Factory(
        HelloGrpcService,
        hello_service=hello_service,
    )


def serve():
    container = Container()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    register_grpc_services(container, server)

    server.add_insecure_port(f'{SERVER_HOST}:{SERVER_PORT}')
    print(f"Starting server on {SERVER_HOST}:{SERVER_PORT}")

    server.start()
    try:
        while True:
            time.sleep(SECONDS_IN_DAY)
    except KeyboardInterrupt:
        server.stop(0)


def register_grpc_services(container: Container, server: grpc.Server):
    hello_grpc_service = container.hello_grpc_service()
    hello_pb2_grpc.add_HelloWorldServicer_to_server(hello_grpc_service, server)


if __name__ == '__main__':
    serve()

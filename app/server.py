import grpc
from concurrent import futures
import time
from app.proto import hello_pb2_grpc
from app.services.hello_service import HelloWorldService


SERVER_HOST = 'localhost'
SERVER_PORT = 50051


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hello_pb2_grpc.add_HelloWorldServicer_to_server(HelloWorldService(), server)

    server.add_insecure_port(f'{SERVER_HOST}:{SERVER_PORT}')

    # Print the connection path when the server starts
    print(f'Starting server on {SERVER_HOST}:{SERVER_PORT}...')
    print(f'Connection path: http://{SERVER_HOST}:{SERVER_PORT}')

    server.start()
    try:
        while True:
            time.sleep(86400)  # Keeps the server running indefinitely
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()

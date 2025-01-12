from app.proto import hello_pb2, hello_pb2_grpc
import app.domain.services.IHelloService as IHelloService


class HelloGrpcService(hello_pb2_grpc.HelloWorldServicer):
    def __init__(self, hello_service: IHelloService):
        self.hello_service = hello_service

    def SayHello(self, request, context):
        response: str = self.hello_service.say_hello(request.name)
        return hello_pb2.HelloResponse(message=response)

    def Echo(self, request, context):
        response: str = self.hello_service.echo(request.text)
        return hello_pb2.EchoResponse(text=response)

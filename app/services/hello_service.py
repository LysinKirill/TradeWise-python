from app.proto import hello_pb2, hello_pb2_grpc


class HelloWorldService(hello_pb2_grpc.HelloWorldServicer):
    def SayHello(self, request, context):
        return hello_pb2.HelloResponse(message=f"Hello, {request.name}!")

    def Echo(self, request, context):
        return hello_pb2.EchoResponse(text=request.text)

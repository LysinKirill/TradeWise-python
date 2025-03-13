import grpc
from app.infrastructure.GrpcContextAccessor import GrpcContextAccessor


class ContextInterceptor(grpc.ServerInterceptor):
    def __init__(self, context_accessor: GrpcContextAccessor):
        self._context_accessor = context_accessor

    def intercept_service(self, continuation, handler_call_details):
        """
        Intercepts the gRPC call and sets the context in the context accessor.
        """
        method_handler = continuation(handler_call_details)

        if not method_handler:
            return None

        def intercept_handler(request, context):
            self._context_accessor.set_context(context)

            return method_handler.unary_unary(request, context)

        return grpc.unary_unary_rpc_method_handler(
            intercept_handler,
            request_deserializer=method_handler.request_deserializer,
            response_serializer=method_handler.response_serializer,
        )
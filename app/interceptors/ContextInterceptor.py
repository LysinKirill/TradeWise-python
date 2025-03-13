import grpc
from app.infrastructure.GrpcContextAccessor import GrpcContextAccessor


class ContextInterceptor(grpc.ServerInterceptor):
    def __init__(self, context_accessor: GrpcContextAccessor):
        self._context_accessor = context_accessor

    def intercept_service(self, continuation, handler_call_details):
        """
        Intercepts the gRPC call and sets the context in the context accessor.
        """
        # Get the original method handler from the continuation
        method_handler = continuation(handler_call_details)

        # If there's no method handler, return None
        if not method_handler:
            return None

        # Create a wrapper for the unary-unary method handler
        def intercept_handler(request, context):
            # Set the context in the context accessor
            self._context_accessor.set_context(context)

            # Call the original unary-unary handler
            return method_handler.unary_unary(request, context)

        # Return a new RpcMethodHandler with the wrapped handler
        return grpc.unary_unary_rpc_method_handler(
            intercept_handler,
            request_deserializer=method_handler.request_deserializer,
            response_serializer=method_handler.response_serializer,
        )
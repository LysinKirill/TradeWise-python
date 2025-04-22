from grpc import aio
import grpc

class ContextInterceptor(aio.ServerInterceptor):
    def __init__(self, context_accessor):
        self._context_accessor = context_accessor

    async def intercept_service(self, continuation, handler_call_details):
        handler = await continuation(handler_call_details)

        if not handler or not hasattr(handler, 'unary_unary'):
            return handler

        if handler.request_streaming and handler.response_streaming:
            async def bidi_wrapper(request_iterator, context):
                self._context_accessor.set_context(context)
                async for response in handler.stream_stream(request_iterator, context):
                    yield response
            return grpc.stream_stream_rpc_method_handler(
                bidi_wrapper,
                handler.request_deserializer,
                handler.response_serializer
            )

        elif handler.request_streaming:
            async def client_stream_wrapper(request_iterator, context):
                self._context_accessor.set_context(context)
                return await handler.stream_unary(request_iterator, context)
            return grpc.stream_unary_rpc_method_handler(
                client_stream_wrapper,
                handler.request_deserializer,
                handler.response_serializer
            )

        elif handler.response_streaming:
            async def server_stream_wrapper(request, context):
                self._context_accessor.set_context(context)
                async for response in handler.unary_stream(request, context):
                    yield response
            return grpc.unary_stream_rpc_method_handler(
                server_stream_wrapper,
                handler.request_deserializer,
                handler.response_serializer
            )

        else:
            async def unary_wrapper(request, context):
                self._context_accessor.set_context(context)
                return await handler.unary_unary(request, context)
            return grpc.unary_unary_rpc_method_handler(
                unary_wrapper,
                handler.request_deserializer,
                handler.response_serializer
            )
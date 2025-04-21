from app.infrastructure.GrpcContextAccessor import GrpcContextAccessor
from grpc import aio
from typing import Any, Callable, Optional
import grpc


class ContextInterceptor(aio.ServerInterceptor):
    def __init__(self, context_accessor: GrpcContextAccessor):
        self._context_accessor = context_accessor

    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], Any],
        handler_call_details: grpc.HandlerCallDetails
    ) -> Any:
        handler = await continuation(handler_call_details)

        if not handler:
            return None

        if handler.request_streaming and handler.response_streaming:
            # Bidirectional streaming
            async def bidi_stream_handler(request_iterator, context):
                self._context_accessor.set_context(context)
                async for response in handler.stream_stream(request_iterator, context):
                    yield response
            return bidi_stream_handler

        elif handler.request_streaming:
            # Client streaming
            async def client_stream_handler(request_iterator, context):
                self._context_accessor.set_context(context)
                return await handler.stream_unary(request_iterator, context)
            return client_stream_handler

        elif handler.response_streaming:
            # Server streaming
            async def server_stream_handler(request, context):
                self._context_accessor.set_context(context)
                async for response in handler.unary_stream(request, context):
                    yield response
            return server_stream_handler

        else:
            # Unary-unary
            async def unary_unary_handler(request, context):
                self._context_accessor.set_context(context)
                return await handler.unary_unary(request, context)
            return unary_unary_handler
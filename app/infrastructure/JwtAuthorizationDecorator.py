from functools import wraps
import grpc
import logging
import sys


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger("[Authorization]")


def jwt_authorization(func):
    """
    Decorator to enforce JWT Bearer authorization for gRPC methods.
    """
    @wraps(func)
    async def wrapper(self, request, context):
        try:
            headers = {key for key, value in context.invocation_metadata()}
            if "authorization" not in headers:
                await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing \"Authorization\" header")
                return
            elif await self.claim_values_service.get_email() is None:
                await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or missing JWT token")
                return

        except Exception as e:
            logger.error(e)
            if context.code() != grpc.StatusCode.UNAUTHENTICATED:
                await context.abort(grpc.StatusCode.UNAUTHENTICATED, f"Authorization failed")
            raise grpc.RpcError()

        return await func(self, request, context)

    return wrapper

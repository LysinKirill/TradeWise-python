from functools import wraps
import grpc
import logging
import sys

from app.domain.exceptions.authorization.UnauthorizedException import UnauthorizedException

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
                raise UnauthorizedException("Missing authorization header")
            elif await self.claim_values_service.get_email() is None:
                raise UnauthorizedException("Invalid or missing JWT token")

        except Exception:
            raise UnauthorizedException("Authorization failed")

        return await func(self, request, context)

    return wrapper

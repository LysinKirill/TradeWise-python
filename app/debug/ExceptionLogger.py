from functools import wraps
import grpc
import sys
import logging
from app.domain.exceptions.user.MissingValueException import MissingValueException
from app.domain.exceptions.user.NoAccountsExistException import NoAccountsExistException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger("[ExceptionLogger]")

def exception_handler(func):
    @wraps(func)
    async def wrapper(self, request, context):
        try:
            return await func(self, request, context)
        except (NoAccountsExistException, MissingValueException) as e:
            logger.warning(f"Business exception in {func.__name__}: {str(e)}")
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
        except grpc.RpcError as e:
            logger.error(
                f"RPC Error in {func.__name__}: "
                f"Code={e.code()}, Details={e.details()}",
                exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in {func.__name__}",
                exc_info=True
            )
            await context.abort(
                grpc.StatusCode.INTERNAL,
                f"Internal server error: {str(e)}"
            )
    return wrapper

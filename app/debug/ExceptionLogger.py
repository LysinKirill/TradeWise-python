from functools import wraps
import grpc
import sys
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger("[ExceptionLogger]")

def exception_logging(func):
    @wraps(func)
    def wrapper(self, request, context):
        try:
            return func(self, request, context)
        except Exception as e:
            if context.code() != grpc.StatusCode.OK:
                logger.error(f"RPC Exception: Status code: {context.code()}, Details: {context.details()}")
                raise
            logger.error(f"Exception in {func.__name__}: {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error occurred: {str(e)}")
    return wrapper

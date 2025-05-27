from functools import wraps
import grpc
import sys
import logging
from app.domain.BusinessErrorCode import BusinessErrorCode
from app.domain.BusinessException import BusinessException
from app.domain.exceptions.authorization.UnauthorizedException import UnauthorizedException
from app.domain.exceptions.user.MissingValueException import MissingValueException
from app.domain.exceptions.user.NoAccountsExistException import NoAccountsExistException
from app.domain.exceptions.validation.ValidationException import ValidationException

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
        except UnauthorizedException:
            logger.warning(f"Unauthorized exception when trying to execute {func.__name__}")
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Unauthorized")
        except (NoAccountsExistException, MissingValueException) as e:
            logger.warning(f"Business exception in {func.__name__}: {str(e)}")
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
        except ValidationException as e:
            logger.warning(f"Validation exception in {func.__name__}: {str(e)}")
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"{e}; Validation error code: {e.code}")
        except BusinessException as e:
            logger.warning(f"Business exception in {func.__name__}: {str(e)}")
            await context.abort(_business_error_code_to_grpc(e.code), f"{e}; Business error code: {e.code}")
        except grpc.RpcError as e:
            logger.error(
                f"RPC Error in {func.__name__}: {str(e)}",
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


def _business_error_code_to_grpc(code: BusinessErrorCode):
    match code:
        case BusinessErrorCode.Unknown: return grpc.StatusCode.UNKNOWN
        case BusinessErrorCode.ModelNotFound: return grpc.StatusCode.NOT_FOUND
        case BusinessErrorCode.ExecutionNotFound: return grpc.StatusCode.NOT_FOUND
        case BusinessErrorCode.UserNotFound: return grpc.StatusCode.NOT_FOUND
        case BusinessErrorCode.BacktestNotFound: return grpc.StatusCode.NOT_FOUND
        case BusinessErrorCode.InvalidExecutionStateTransition: return grpc.StatusCode.INVALID_ARGUMENT
        case BusinessErrorCode.InvalidBacktestStateTransition: return grpc.StatusCode.INVALID_ARGUMENT
        case BusinessErrorCode.BacktestAlreadyQueued: return grpc.StatusCode.INVALID_ARGUMENT
        case BusinessErrorCode.InvestApiKeyNotSet: return grpc.StatusCode.PERMISSION_DENIED

    return grpc.StatusCode.UNKNOWN
from functools import wraps
import grpc


def exception_logging(func):
    @wraps(func)
    def wrapper(self, request, context):
        try:
            return func(self, request, context)
        except Exception as e:
            if context.code() != grpc.StatusCode.OK:
                print(f"RPC Exception: Status code: {context.code()}, Details: {context.details()}")
                raise
            print(f"Exception in {func.__name__}: {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error occurred: {str(e)}")
    return wrapper

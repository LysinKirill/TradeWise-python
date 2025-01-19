import grpc


def exception_logging(func):
    def wrapper(self, request, context):
        try:
            return func(self, request, context)
        except Exception as e:
            print(f"Exception in {func.__name__}: {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error occurred: {str(e)}")
    return wrapper

from functools import wraps
import grpc


def jwt_authorization(func):
    """
    Decorator to enforce JWT Bearer authorization for gRPC methods.
    """

    @wraps(func)
    def wrapper(self, request, context):
        try:
            headers = {key for key, value in context.invocation_metadata()}
            if "authorization" not in headers:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing \"Authorization\" header")
                return
            elif self.claim_values_service.get_email() is None:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or missing JWT token")
                return

            return func(self, request, context)
        except grpc.RpcError:
            raise
        except Exception:
            if context.code() != grpc.StatusCode.UNAUTHENTICATED:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, f"Authorization failed")
            raise grpc.RpcError()

    return wrapper

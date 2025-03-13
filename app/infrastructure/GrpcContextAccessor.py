import grpc
import threading


class GrpcContextAccessor:
    def __init__(self):
        self._local = threading.local()

    def set_context(self, context: grpc.ServicerContext) -> None:
        """
        Set the current gRPC context.
        :param context: The gRPC context.
        """
        self._local.context = context

    def get_context(self) -> grpc.ServicerContext:
        """
        Get the current gRPC context.
        :return: The current gRPC context.
        """
        if not hasattr(self._local, "context"):
            raise RuntimeError("No gRPC context is set")
        return self._local.context
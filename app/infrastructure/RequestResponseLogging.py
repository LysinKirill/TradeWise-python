from functools import wraps


def request_response_logging(logger_prompt: str | None = None):
    def add_padding(obj, padding: str) -> str:
        s = str(obj)
        return padding + s.replace('\n', f'\n{padding}')

    if logger_prompt is None:
        logger_prompt = "[REQUEST_RESPONSE_LOGGING]"

    def request_response_decorator(func):
        @wraps(func)
        def wrapper(self, request, context):
            if logger_prompt is not None:
                print(logger_prompt)
            print(f"Request to {func.__name__}: \n{add_padding(request, '    ')}")
            response = func(self, request, context)
            print(f"Response from {func.__name__}: \n{add_padding(response, '    ')}")

            return response
        return wrapper
    return request_response_decorator
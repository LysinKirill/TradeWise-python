import sys
import logging

from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger("[RequestResponseLogging]")

def request_response_logging(logger_prompt: str | None = None):
    def add_padding(obj, padding: str) -> str:
        s = str(obj)
        return padding + s.replace('\n', f'\n{padding}')

    if logger_prompt is None:
        logger_prompt = "[REQUEST_RESPONSE_LOGGING]"

    def request_response_decorator(func):
        @wraps(func)
        async def wrapper(self, request, context):
            if logger_prompt is not None:
                logger.info(logger_prompt)
            logger.info(f"Request to {func.__name__}: \n{add_padding(request, '    ')}")
            response = await func(self, request, context)
            logger.info(f"Response from {func.__name__}: \n{add_padding(response, '    ')}")
            return response
        return wrapper
    return request_response_decorator
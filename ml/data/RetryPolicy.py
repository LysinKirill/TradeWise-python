from collections.abc import Callable

from ml.data.configuration.BackoffStrategy import BackoffStrategy
from ml.data.configuration.RetryPolicyConfiguration import RetryPolicyConfiguration
import asyncio
import logging
import sys


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

class RetryPolicy:
    def __init__(
        self,
        configuration: RetryPolicyConfiguration,
    ):
        self.logger = logging.getLogger("[RetryPolicy]")
        self.configuration = configuration

    async def invoke(
            self,
            func: Callable,
            argument: any,
            verbose: bool = False) -> any:
        for attempt in range(self.configuration.allowed_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(argument)
                    if result is None:
                        raise ValueError("Function returned no value")
                    return result
                else:
                    result = func(argument)
                    if result is None:
                        raise ValueError("Function returned no value")
                    return result
            except Exception as e:
                attempt_number = attempt + 1
                initial_delay = self.configuration.initial_delay_in_seconds
                if verbose:
                    self.logger.error(f"An error occurred executing function '{func.__name__}': {e}. Attempt #{attempt_number}")

                delay: float = 0
                match self.configuration.backoff_strategy:
                    case BackoffStrategy.Fixed: delay = initial_delay
                    case BackoffStrategy.Linear: delay = initial_delay * attempt_number
                    case BackoffStrategy.Exponential: delay = initial_delay * (2 ** attempt)

                await asyncio.sleep(delay)
                continue

        return None
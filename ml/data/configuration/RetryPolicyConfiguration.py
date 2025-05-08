from dataclasses import dataclass

from ml.data.configuration.BackoffStrategy import BackoffStrategy


@dataclass
class RetryPolicyConfiguration:
    initial_delay_in_seconds: float
    allowed_attempts: int
    backoff_strategy: BackoffStrategy
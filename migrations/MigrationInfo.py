from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MigrationInfo:
    id: int
    version: int
    applied_on: datetime
    description: str
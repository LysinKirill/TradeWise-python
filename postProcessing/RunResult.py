from enum import Enum


class RunResult(Enum):
    UNKNOWN = "❓"
    OK = "✅"
    FAIL = "⛔"
    IN_PROGRESS = "⏳"

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value

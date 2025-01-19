from abc import ABC, abstractmethod


class PostProcessor(ABC):
    processor_name: str | None = None
    @abstractmethod
    def perform_post_process(self) -> None:
        pass
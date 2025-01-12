from abc import ABC, abstractmethod


class PostProcessor(ABC):
    @abstractmethod
    def perform_post_process(self) -> None:
        pass
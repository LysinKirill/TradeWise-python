from abc import ABC, abstractmethod


class IHelloService(ABC):
    @abstractmethod
    def say_hello(self, name: str | None) -> str:
        pass

    @abstractmethod
    def echo(self, message: str | None) -> str:
        pass

from app.domain.services.IHelloService import IHelloService


class HelloService(IHelloService):
    def say_hello(self, name: str | None) -> str:
        if name is None:
            return "Hello!"
        return f"Hello"

    def echo(self, message: str | None) -> str:
        return message


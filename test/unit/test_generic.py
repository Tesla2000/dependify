import unittest
from typing import Generic
from typing import TypeVar

from dependify import DependencyInjectionContainer
from dependify import wired

T = TypeVar("T")


class TestGeneric(unittest.TestCase):
    def setUp(self):
        self.container = DependencyInjectionContainer()

    def test_wired_basic_functionality(self):
        @wired
        class Repo(Generic[T]):
            def __init__(self, value: T):
                self.value = value

        class User:
            def __init__(self):
                self.name = "Alice"

        @wired(container=self.container)
        class MyService:
            repo: Repo[User]

        service = self.container.resolve_optional(MyService)
        assert isinstance(service, MyService)
        assert isinstance(service.repo, Repo)

    def test_wired_basic_functionality_no_args(self):
        @wired
        class Repo(Generic[T]):
            pass

        class User:
            pass

        @wired(container=self.container)
        class MyService:
            repo: Repo[User]

        service = self.container.resolve_optional(MyService)
        assert isinstance(service, MyService)
        assert isinstance(service.repo, Repo)

    def test_wired_basic_functionality_multiple_args(self):
        @wired
        class Repo(Generic[T]):
            pass

        @wired(container=self.container)
        class User:
            pass

        @wired(container=self.container)
        class MyService:
            user1: User
            repo: Repo[User]
            user2: User

        service = self.container.resolve_optional(MyService)
        assert isinstance(service, MyService)
        assert isinstance(service.repo, Repo)
        assert isinstance(service.user1, User)
        assert isinstance(service.user2, User)

    def test_wired_basic_functionality_implementation(self):
        @wired
        class Repo(Generic[T]):
            pass

        @wired(container=self.container)
        class Name:
            pass

        @wired(container=self.container)
        class User:
            name: Name

        @wired(container=self.container)
        class MyService:
            user1: User
            repo: Repo[User]
            user2: User

        service = self.container.resolve_optional(MyService)
        assert isinstance(service, MyService)
        assert isinstance(service.repo, Repo)
        assert isinstance(service.user1, User)
        assert isinstance(service.user2, User)

    def test_overwritten(self):
        @wired
        class Repo(Generic[T]):
            pass

        @wired(container=self.container)
        class User:
            pass

        @wired(container=self.container)
        class UserRepo(Repo[User]):
            pass

        @wired(container=self.container)
        class MyService:
            repo: Repo[User]

        service = self.container.resolve_optional(MyService)
        assert isinstance(service, MyService)
        assert isinstance(service.repo, UserRepo)


if __name__ == "__main__":
    unittest.main()

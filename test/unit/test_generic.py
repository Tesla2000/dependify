import unittest
from abc import ABC
from abc import abstractmethod
from typing import ClassVar
from typing import Generic
from typing import TypeVar

from dependify import DependencyInjectionContainer
from dependify import wired

T = TypeVar("T")


class TestGeneric(unittest.TestCase):
    def setUp(self):
        self.container = DependencyInjectionContainer()

    def test_wired_basic_functionality(self):
        @wired(container=self.container)
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
        @wired(container=self.container)
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
        @wired(container=self.container)
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
        @wired(container=self.container)
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
        @wired(container=self.container)
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

    def test_generic_dependency(self):
        class AbstractClass(ABC):
            @abstractmethod
            def foo(self):
                pass

        @wired(container=self.container)
        class Impl1(AbstractClass):
            def foo(self):
                return "impl1"

        @wired(container=self.container)
        class Impl2(AbstractClass):
            def foo(self):
                return "impl2"

        BoundT = TypeVar("BoundT", bound=AbstractClass)

        class Service(Generic[BoundT]):
            impl: BoundT

        @wired(container=self.container)
        class ServiceImpl(Service[Impl2]):
            pass

        service = self.container.resolve_optional(ServiceImpl)
        assert isinstance(service, Service)
        assert isinstance(service.impl, Impl2)

    def test_generic_kwargs(self):
        @wired(container=self.container)
        class Repo(Generic[T]):
            def __init__(self, value: T):
                self.value = value

        class User:
            def __init__(self, name: str = "Alice"):
                self.name = name

        user_name = "Bob"

        @wired(container=self.container)
        class MyService:
            repo: Repo[User]
            user: User = User(name=user_name)

        service = self.container.resolve_optional(MyService)
        assert isinstance(service, MyService)
        assert isinstance(service.repo, Repo)
        assert isinstance(service.user, User)
        assert service.user.name == user_name

    def test_generic_class_var(self):
        @wired(container=self.container)
        class Repo(Generic[T]):
            def __init__(self, value: T):
                self.value = value

        class User:
            def __init__(self, name: str = "Alice"):
                self.name = name

        user_name = "Bob"

        @wired(container=self.container)
        class MyService:
            repo: Repo[User]
            user: ClassVar[User] = User(name=user_name)

        service = self.container.resolve_optional(MyService)
        assert isinstance(service, MyService)
        assert isinstance(service.repo, Repo)
        assert isinstance(service.user, User)
        assert service.user.name == user_name

    def test_generic_not_in_container_negative(self):
        """Negative test: Generic class registered in different container should not be resolvable"""
        other_container = DependencyInjectionContainer()

        @wired(container=other_container)  # Registered in OTHER container
        class Repo(Generic[T]):
            pass

        class User:
            pass

        @wired(container=self.container)  # Registered in SELF container
        class MyService:
            repo: Repo[User]  # Trying to use Repo from other container

        # Should fail because Repo is not in self.container
        with self.assertRaises(TypeError) as context:
            self.container.resolve_optional(MyService)

        # Verify the error message mentions the missing argument
        assert "Missing arguments" in str(context.exception)
        assert "repo" in str(context.exception)


if __name__ == "__main__":
    unittest.main()

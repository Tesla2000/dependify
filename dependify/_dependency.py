from typing import Any


class Dependency:
    """
    Represents a dependency that can be resolved and injected into other classes or functions.
    """

    cached: bool = False
    autowire: bool = True
    instance: Any = None
    target: Any

    def __init__(
        self,
        target: Any,
        cached: bool = False,
        autowire: bool = True,
    ):
        """
        Initializes a new instance of the `Dependency` class.

        Args:
            target (Any): The target function, class or defealt value to resolve the dependency.
            cached (bool, optional): Indicates whether the dependency should be cached. Defaults to False.
            autowire (bool, optional): Indicates whether the dependency arguments should be autowired. Defaults to True.
        """
        self.target = target
        self.cached = cached
        self.autowire = autowire

    def resolve(self, *args, **kwargs):
        """
        Resolves the dependency by invoking the target function or creating an instance of the target class.

        Args:
            *args: Variable length argument list to be passed to the target function or class constructor.
            **kwargs: Arbitrary keyword arguments to be passed to the target function or class constructor.

        Returns:
            The resolved dependency object.
        """
        if self.cached and self.instance:
            return self.instance
        if callable(self.target):
            self.instance = self.target(*args, **kwargs)
        else:
            self.instance = self.target
        return self.instance

    def __eq__(self, other):
        """
        Check if two Dependency objects are equal based on target, cached, and autowire.
        """
        if not isinstance(other, Dependency):
            return False
        return self.target == other.target

    def __hash__(self):
        """
        Generate hash for Dependency object based on target, cached, and autowire.
        """
        return hash((self.target, self.cached, self.autowire))

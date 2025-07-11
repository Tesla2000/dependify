from typing import Any, Callable, Type, Union


class Dependency:
    """
    Represents a dependency that can be resolved and injected into other classes or functions.
    """

    cached: bool = False
    autowire: bool = True
    instance: Any = None
    target: Union[Type, Callable]

    def __init__(
        self,
        target: Union[Type, Callable],
        cached: bool = False,
        autowire: bool = True,
    ):
        """
        Initializes a new instance of the `Dependency` class.

        Args:
            target (Callable|Type): The target function or class to resolve the dependency.
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
        if self.cached:
            if not self.instance:
                self.instance = self.target(*args, **kwargs)
            return self.instance
        return self.target(*args, **kwargs)

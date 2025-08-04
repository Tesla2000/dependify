from collections.abc import Mapping
from inspect import signature
from types import MappingProxyType
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Self
from typing import Type
from typing import Union

from dependify._dependency import Dependency


class DependencyRegistry:
    """
    A class representing a dependency injection registry.

    The `Container` class is responsible for registering and resolving dependencies.
    It allows you to register dependencies by name and resolve them when needed.

    Attributes:
        _dependencies (Dict[Type, Dependency]): A dictionary that stores the registered dependencies.

    Methods:
        __init__(self, dependencies: Dict[str, Dependency]): Initializes a new instance of the `Container` class.
        register_dependency(self, name: Type, dependency: Dependency): Registers a dependency with the specified name.
        register(self, name: Type, target: Type|Callable = None, cached: bool = False, autowired: bool = True): Registers a dependency with the specified name and target.
        resolve(self, name: Type): Resolves a dependency with the specified name.

    """

    _dependencies: Dict[Type, Dependency]

    def __init__(self, dependencies: Optional[Dict[Type, Dependency]] = None):
        """
        Initializes a new instance of the `Container` class.

        Args:
            dependencies (Dict[Type, Dependency], optional): A dictionary of dependencies to be registered. Defaults to an empty dictionary.
        """
        self._dependencies = dependencies or {}

    def register_dependency(self, name: Type, dependency: Dependency) -> None:
        """
        Registers a dependency with the specified name.

        Args:
            name (Type): The name of the dependency.
            dependency (Dependency): The dependency to be registered.
        """
        self._dependencies[name] = dependency

    def register(
        self,
        name: Type,
        target: Union[Type, Callable] = None,
        cached: bool = False,
        autowired: bool = True,
    ) -> None:
        """
        Registers a dependency with the specified name and target.

        Args:
            name (Type): The name of the dependency.
            target (Type|Callable, optional): The target type or callable to be resolved as the dependency. Defaults to None.
            cached (bool, optional): Indicates whether the dependency should be cached. Defaults to False.
            autowired (bool, optional): Indicates whether the dependency should be resolved automatically. Defaults to True.
        """
        if not target:
            target = name
        self.register_dependency(name, Dependency(target, cached, autowired))

    def resolve(self, name: Type) -> Any:
        """
        Resolves a dependency with the specified name.

        Args:
            name (Type): The name of the dependency.

        Returns:
            Any: The resolved dependency, or None if the dependency is not registered.
        """
        if name not in self._dependencies:
            return None

        dependency = self._dependencies[name]

        if not dependency.autowire:
            return dependency.resolve()

        kwargs = {}
        parameters = signature(dependency.target).parameters

        for name, parameter in parameters.items():
            if parameter.annotation in self._dependencies:
                kwargs[name] = self.resolve(parameter.annotation)

        return dependency.resolve(**kwargs)

    @property
    def dependencies(self) -> Mapping[Type, Dependency]:
        """
        Returns a read-only view of the registry's dependencies.
        """
        return MappingProxyType(self._dependencies)

    def __contains__(self, name: Type) -> bool:
        return name in self._dependencies

    def clear(self):
        self._dependencies = {}

    def __add__(self, other: "DependencyRegistry") -> "DependencyRegistry":
        if not isinstance(other, DependencyRegistry):
            raise ValueError(
                f"Only {DependencyRegistry.__name__} can be added to {type(self).__name__}"
            )
        return type(self)(
            dependencies={**other.dependencies, **self.dependencies}
        )

    def __enter__(self) -> Self:
        self._dep_cp = self._dependencies.copy()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> bool:
        self._dependencies = self._dep_cp
        del self._dep_cp
        return False

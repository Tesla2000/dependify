from collections.abc import Mapping
from contextlib import suppress
from inspect import signature
from types import MappingProxyType
from typing import Callable
from typing import Dict
from typing import get_args
from typing import get_origin
from typing import Optional
from typing import Self
from typing import Type
from typing import TypeVar
from typing import Union

from dependify._dependency import Dependency

ResolvedType = TypeVar("ResolvedType")


class DependencyInjectionContainer:
    """
    A class representing a dependency injection container.

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
    _dep_cp: list[Dict[Type, Dependency]]

    def __init__(self, dependencies: Optional[Dict[Type, Dependency]] = None):
        """
        Initializes a new instance of the `Container` class.

        Args:
            dependencies (Dict[Type, Dependency], optional): A dictionary of dependencies to be registered. Defaults to an empty dictionary.
        """
        self._dependencies = dependencies or {}
        self._dep_cp = []

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

    def resolve(self, name: Type[ResolvedType], **kwargs) -> ResolvedType:
        """
        Resolves a dependency with the specified name.

        Args:
            name (Type): The name of the dependency.

        Returns:
            Any: The resolved dependency, or None if the dependency is not registered.
        """
        resolved = self.resolve_optional(name, **kwargs)
        if resolved is None:
            raise ValueError(f"{name=} couldn't be resolved")
        return resolved

    def resolve_optional(
        self, name: Type[ResolvedType], **kwargs
    ) -> Optional[ResolvedType]:
        """
        Resolves a dependency with the specified name.

        Args:
            name (Type): The name of the dependency.

        Returns:
            Any: The resolved dependency, or None if the dependency is not registered.
        """
        if name not in self._dependencies:
            origin = get_origin(name)
            if origin is None:
                return None

            # Check if there's a registered subclass of the generic type
            # For example, if looking for Repo[User], check if UserRepo is registered
            # where UserRepo is a subclass of Repo[User]
            for registered_type in self._dependencies:
                if not isinstance(registered_type, type):
                    continue
                if any(
                    map(
                        name.__eq__,
                        getattr(registered_type, "__orig_bases__", ()),
                    )
                ):
                    # Found a registered subclass with matching generic base
                    with suppress(TypeError, AttributeError):
                        return self.resolve_optional(registered_type, **kwargs)

            # Try to resolve the origin class
            if origin in self._dependencies:
                # The generic base class is registered in this container
                dependency = self._dependencies[origin]
                origin_instance_factory = dependency.target
            else:
                # Not registered, but we can still try to use the class directly
                origin_instance_factory = origin

            resolved_args = [
                self.resolve_optional(arg) or arg() for arg in get_args(name)
            ]
            if all(resolved_args):
                return origin_instance_factory(*resolved_args)
            return None

        dependency = self._dependencies[name]

        if not dependency.autowire:
            return dependency.resolve()

        annotation_kwargs = {}
        parameters = signature(dependency.target).parameters

        for name, parameter in parameters.items():
            if parameter.annotation in self._dependencies:
                annotation_kwargs[name] = self.resolve_optional(
                    parameter.annotation
                )
        annotation_kwargs.update(kwargs)
        return dependency.resolve(**annotation_kwargs)

    @property
    def dependencies(self) -> Mapping[Type, Dependency]:
        """
        Returns a read-only view of the container's dependencies.
        """
        return MappingProxyType(self._dependencies)

    def __contains__(self, name: Type) -> bool:
        return name in self._dependencies

    def clear(self):
        self._dependencies = {}

    def copy(self) -> Self:
        return type(self)(dependencies=dict(self.dependencies))

    def __add__(
        self, other: "DependencyInjectionContainer"
    ) -> "DependencyInjectionContainer":
        if not isinstance(other, DependencyInjectionContainer):
            raise ValueError(
                f"Only {DependencyInjectionContainer.__name__} can be added to {type(self).__name__}"
            )
        return type(self)(
            dependencies={**other.dependencies, **self.dependencies}
        )

    def __enter__(self) -> Self:
        self._dep_cp.append(self._dependencies.copy())
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> bool:
        self._dependencies = self._dep_cp.pop()
        return False

from contextvars import ContextVar
from inspect import signature
from types import MappingProxyType
from typing import Callable
from typing import Dict
from typing import List
from typing import Mapping
from typing import Optional
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

    _base_dependencies: Dict[Type, Dependency]
    _context_dependencies: ContextVar[Optional[Dict[Type, Dependency]]]
    _context_stack: ContextVar[List[Dict[Type, Dependency]]]

    def __init__(self, dependencies: Optional[Dict[Type, Dependency]] = None):
        """
        Initializes a new instance of the `Container` class.

        Args:
            dependencies (Dict[Type, Dependency], optional): A dictionary of dependencies to be registered. Defaults to an empty dictionary.
        """
        self._base_dependencies = dependencies or {}
        self._context_dependencies = ContextVar("dependencies", default=None)
        self._context_stack = ContextVar("dep_stack", default=None)

    @property
    def _dependencies(self) -> Dict[Type, Dependency]:
        """
        Returns the current dependencies for this context.
        If in a context manager, returns the context-specific dependencies.
        Otherwise, returns the base dependencies.
        """
        stack = self._context_stack.get()
        if stack and len(stack) > 0:
            return stack[-1]
        return self._base_dependencies

    @_dependencies.setter
    def _dependencies(self, value: Dict[Type, Dependency]) -> None:
        """
        Sets the dependencies for the current context.
        """
        stack = self._context_stack.get()
        if stack:
            stack[-1] = value
        else:
            self._base_dependencies = value

    @property
    def _dep_cp(self) -> List[Dict[Type, Dependency]]:
        """
        Returns the dependency stack for this context.
        """
        stack = self._context_stack.get()
        if stack is None:
            stack = []
            self._context_stack.set(stack)
        return stack

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
        target: Union[Callable[[], Type]] = None,
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

    def copy(self) -> "DependencyInjectionContainer":
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

    def __enter__(self) -> "DependencyInjectionContainer":
        self._dep_cp.append(self._dependencies.copy())
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> bool:
        stack = self._context_stack.get()
        if stack:
            stack.pop()
        return False

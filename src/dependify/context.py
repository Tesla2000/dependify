from typing import Callable, Type, Union

from .dependency import Dependency
from .dependency_registry import DependencyRegistry

_registry = DependencyRegistry()


# Shortcuts
def register(
    name: Type,
    target: Union[Type, Callable] = None,
    cached: bool = False,
    autowired: bool = True,
    registry: DependencyRegistry = _registry,
):
    """
    Registers a dependency with the specified name and target.
    """
    return registry.register(name, target, cached, autowired)


def register_dependency(
    name: Type,
    dependency: Dependency,
    registry: DependencyRegistry = _registry,
):
    """
    Registers a dependency with the specified name.
    """
    return registry.register_dependency(name, dependency)


def resolve(name: Type):
    """
    Resolves a dependency with the specified name.
    """
    return _registry.resolve(name)


def has(name: Type):
    """
    Checks if a dependency with the specified name exists.
    """
    return _registry.has(name)


def dependencies():
    """
    Returns the dependencies in the registry.
    """
    return _registry.dependencies()

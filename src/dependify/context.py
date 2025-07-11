from typing import Callable, Type, Union

from .dependency import Dependency
from .dependency_registry import DependencyRegistry

_container = DependencyRegistry()


# Shortcuts
def register(
    name: Type,
    target: Union[Type, Callable] = None,
    cached: bool = False,
    autowired: bool = True,
    container: DependencyRegistry = _container,
):
    """
    Registers a dependency with the specified name and target.
    """
    return container.register(name, target, cached, autowired)


def register_dependency(
    name: Type,
    dependency: Dependency,
    container: DependencyRegistry = _container,
):
    """
    Registers a dependency with the specified name.
    """
    return container.register_dependency(name, dependency)


def resolve(name: Type):
    """
    Resolves a dependency with the specified name.
    """
    return _container.resolve(name)


def has(name: Type):
    """
    Checks if a dependency with the specified name exists.
    """
    return _container.has(name)


def dependencies():
    """
    Returns the dependencies in the container.
    """
    return _container.dependencies()

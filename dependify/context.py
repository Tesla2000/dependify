from typing import Callable
from typing import Type
from typing import Union

from dependify._dependency import Dependency
from dependify.dependency_registry import DependencyRegistry

default_registry = DependencyRegistry()


# Shortcuts
def register(
    name: Type,
    target: Union[Type, Callable] = None,
    cached: bool = False,
    autowired: bool = True,
    registry: DependencyRegistry = default_registry,
):
    """
    Registers a dependency with the specified name and target.
    """
    return registry.register(name, target, cached, autowired)


def register_dependency(
    name: Type,
    dependency: Dependency,
    registry: DependencyRegistry = default_registry,
):
    """
    Registers a dependency with the specified name.
    """
    return registry.register_dependency(name, dependency)


def resolve(name: Type):
    """
    Resolves a dependency with the specified name.
    """
    return default_registry.resolve(name)


def has(name: Type):
    """
    Checks if a dependency with the specified name exists.
    """
    return default_registry.has(name)


def dependencies():
    """
    Returns the dependencies in the registry.
    """
    return default_registry.dependencies()

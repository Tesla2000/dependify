from typing import Callable
from typing import Type
from typing import Union

from dependify.dependencies import Dependency
from dependify.dependency_registry import DependencyRegistry

registry = DependencyRegistry()


# Shortcuts
def register(
    name: Type,
    target: Union[Type, Callable] = None,
    cached: bool = False,
    autowired: bool = True,
    registry_: DependencyRegistry = registry,
):
    """
    Registers a dependency with the specified name and target.
    """
    return registry_.register(name, target, cached, autowired)


def register_dependency(
    name: Type,
    dependency: Dependency,
    registry_: DependencyRegistry = registry,
):
    """
    Registers a dependency with the specified name.
    """
    return registry_.register_dependency(name, dependency)


def resolve(name: Type):
    """
    Resolves a dependency with the specified name.
    """
    return registry.resolve(name)


def has(name: Type):
    """
    Checks if a dependency with the specified name exists.
    """
    return registry.has(name)


def dependencies():
    """
    Returns the dependencies in the registry.
    """
    return registry.dependencies()

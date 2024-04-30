from types import MappingProxyType
from typing import Callable, Type

from .dependency import Dependency
from .container import Container


container = Container()


# Shortcuts
def register(name: Type, target: Type|Callable = None, cached: bool = False, autowired: bool = True):
    """
    Registers a dependency with the specified name and target.
    """
    return container.register(name, target, cached, autowired)

def register_dependency(name: Type, dependency: Dependency):
    """
    Registers a dependency with the specified name.
    """
    return container.register_dependency(name, dependency)

def resolve(name: Type):
    """
    Resolves a dependency with the specified name.
    """
    return container.resolve(name)

def has(name: Type):
    """
    Checks if a dependency with the specified name exists.
    """
    return container.has(name)

def dependencies():
    """
    Returns the dependencies in the container.
    """
    return container.dependencies()


from typing import Any
from typing import Type

from dependify._dependency import Dependency
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)
from dependify._dependency_injection_container import NO_TARGET

default_container = DependencyInjectionContainer()


# Shortcuts
def register(
    name: Type,
    target: Any = NO_TARGET,
    cached: bool = False,
    autowired: bool = True,
    container: DependencyInjectionContainer = default_container,
):
    """
    Registers a dependency with the specified name and target.
    """
    return container.register(name, target, cached, autowired)


def register_dependency(
    name: Type,
    dependency: Dependency,
    container: DependencyInjectionContainer = default_container,
):
    """
    Registers a dependency with the specified name.
    """
    return container.register_dependency(name, dependency)


def remove(
    name: Type,
    target: Any = NO_TARGET,
    container: DependencyInjectionContainer = default_container,
):
    """
    Removes a dependency or all dependencies with the specified name.
    """
    return container.remove(name, target)


def resolve(name: Type):
    """
    Resolves a dependency with the specified name.
    """
    return default_container.resolve(name)


def has(name: Type):
    """
    Checks if a dependency with the specified name exists.
    """
    return name in default_container


def dependencies():
    """
    Returns the dependencies in the container.
    """
    return default_container.dependencies()

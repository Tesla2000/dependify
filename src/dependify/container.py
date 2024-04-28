from inspect import signature
from typing import Callable, Type
from .dependency import Dependency


class Container:
    """
    A class representing a dependency injection container.

    The `Container` class is responsible for registering and resolving dependencies.
    It allows you to register dependencies by name and resolve them when needed.

    Attributes:
        dependencies (dict[Type, Dependency]): A dictionary that stores the registered dependencies.

    Methods:
        __init__(self, dependencies: dict[str, Dependency] = {}): Initializes a new instance of the `Container` class.
        register_dependency(self, name: Type, dependency: Dependency): Registers a dependency with the specified name.
        register(self, name: Type, target: Type|Callable = None, cached: bool = False, autowired: bool = True): Registers a dependency with the specified name and target.
        resolve(self, name: Type): Resolves a dependency with the specified name.

    """

    dependencies: dict[Type, Dependency] = {}

    def __init__(self, dependencies: dict[str, Dependency] = {}):
        """
        Initializes a new instance of the `Container` class.

        Args:
            dependencies (dict[str, Dependency], optional): A dictionary of dependencies to be registered. Defaults to an empty dictionary.
        """
        self.dependencies = dependencies

    def register_dependency(self, name: Type, dependency: Dependency):
        """
        Registers a dependency with the specified name.

        Args:
            name (Type): The name of the dependency.
            dependency (Dependency): The dependency to be registered.
        """
        self.dependencies[name] = dependency

    def register(self, name: Type, target: Type|Callable = None, cached: bool = False, autowired: bool = True):
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

    def resolve(self, name: Type):
        """
        Resolves a dependency with the specified name.

        Args:
            name (Type): The name of the dependency.

        Returns:
            Any: The resolved dependency, or None if the dependency is not registered.
        """
        if name not in self.dependencies:
            return None

        dependency = self.dependencies[name]

        if not dependency.autowire:
            return dependency.resolve()
        
        kwargs = {}
        parameters = signature(dependency.target).parameters

        for name, parameter in parameters.items():
            if parameter.annotation in self.dependencies:
                kwargs[name] = self.resolve(parameter.annotation)
            
        return dependency.resolve(**kwargs)


            
        

from functools import wraps
from typing import Callable

from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)

from ._get_existing_annot import get_existing_annot


class Inject:
    """
    Decorator to inject dependencies into a function.
    """

    def __init__(self, container: DependencyInjectionContainer):
        """
        Parameters:
            container (DependencyInjectionContainer): the container used to inject the dependencies.
        """
        self.container = container

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            existing_annotations = get_existing_annot(func, self.container)
            for name, annotation in existing_annotations.items():
                if name not in kwargs:  # Only inject if not already provided
                    kwargs[name] = self.container.resolve(annotation)
            return func(*args, **kwargs)

        return wrapper

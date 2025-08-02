from functools import wraps

from dependify.context import registry
from dependify.dependency_registry import DependencyRegistry

from ._get_existing_annot import get_existing_annot


def inject(_func=None, *, registry_: DependencyRegistry = registry):
    """
    Decorator to inject dependencies into a function.

    Parameters:
        registry_ (DependencyRegistry): the registry used to inject the dependencies. Defaults to module registry.
    """

    def decorated(func):
        @wraps(func)
        def subdecorator(*args, **kwargs):
            for name, annotation in get_existing_annot(
                func, registry_
            ).items():
                if name not in kwargs:  # Only inject if not already provided
                    kwargs[name] = registry_.resolve(annotation)
            return func(*args, **kwargs)

        return subdecorator

    if _func is None:
        return decorated

    else:
        return decorated(_func)

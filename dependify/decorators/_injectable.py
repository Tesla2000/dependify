from typing import Optional
from typing import Type

from dependify.context import default_registry
from dependify.context import register
from dependify.dependency_registry import DependencyRegistry


def injectable(
    _func: Optional[Type] = None,
    *,
    patch: Optional[Type] = None,
    cached=False,
    autowire=True,
    registry: DependencyRegistry = default_registry,
):
    def decorator(func):
        if patch:
            register(patch, func, cached, autowire, registry)
        else:
            register(func, None, cached, autowire, registry)

        return func

    if _func is None:
        return decorator
    else:
        return decorator(_func)

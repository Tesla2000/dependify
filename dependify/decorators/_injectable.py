from typing import Optional
from typing import Type

from dependify._default_container import default_container
from dependify._default_container import register
from dependify._dependency_container import DependencyInjectionContainer


def injectable(
    _func: Optional[Type] = None,
    *,
    patch: Optional[Type] = None,
    cached=False,
    autowire=True,
    container: DependencyInjectionContainer = default_container,
):
    def decorator(func):
        if patch:
            register(patch, func, cached, autowire, container)
        else:
            register(func, None, cached, autowire, container)

        return func

    if _func is None:
        return decorator
    else:
        return decorator(_func)

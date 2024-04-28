from functools import wraps
from inspect import signature
from .container import Container


_container = Container()


def register(name, target=None, cached=False, autowire=True):
    """
    Register a dependency with the container.

    Parameters:
        name (Type): The type of the dependency.
        target (Type|Callable): The target of the dependency.
        cached (bool): Whether the dependency should be cached.
        autowired (bool): Whether the dependency should be autowired.
    """
    _container.register(name, target, cached, autowire)


def set_container(container: Container):
    """
    Set the container to use for dependency injection.

    Parameters:
    container (Container): The container to use.
    """
    _container = container


def get_dependencies(f, container: Container = _container):
    """
    Get the dependencies of a function.

    Parameters:
    f (Callable): The function to get the dependencies of.
    """
    to_inject = {}
    parameters = signature(f).parameters
    for name, parameter in parameters.items():
        if parameter.default != parameter.empty:
            continue

        if parameter.annotation in container.dependencies:
            to_inject[name] = parameter.annotation

    return to_inject
    

def inject(_func=None, *, container=_container):
    """
    Decorator to inject dependencies into a function.

    Parameters:
        container (Container): the container used to inject the dependencies. Defaults to module container.
    """
    def decorated(func):
        @wraps(func)
        def subdecorator(*args, **kwargs):
            for name, dependency in get_dependencies(func, container).items():
                kwargs[name] = _container.resolve(dependency)
            return func(*args, **kwargs)
        return subdecorator
    
    if _func is None:
        return decorated
    
    else:
        return decorated(_func)


def injectable(_func=None, *, patch=None, cached=False, autowire=True):
    """
    Decorator to register a class as an injectable dependency.

    Parameters:
        patch (Type): The type to patch.
        cached (bool): Whether the dependency should be cached.
    """
    def decorator(func):
        if patch:
            register(patch, func, cached, autowire)
        else:
            register(func, None, cached, autowire)

        return func
    
    if _func is None:
        return decorator
    else:
        return decorator(_func)

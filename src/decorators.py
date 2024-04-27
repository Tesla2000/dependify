from functools import wraps
from inspect import signature
from container import Container

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

def get_dependencies(f):
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

        if parameter.annotation in _container.dependencies:
            to_inject[name] = parameter.annotation

    return to_inject
    

def inject(f):
    """
    Decorator to inject dependencies into a function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        for name, dependency in get_dependencies(f).items():
            kwargs[name] = _container.resolve(dependency)
        return f(*args, **kwargs)

    return decorated


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


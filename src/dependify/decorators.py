from functools import partial, wraps
from inspect import Parameter, Signature, signature
from typing import Callable, Optional, Type, TypeVar, Union

from .context import _registry, register
from .dependency_registry import DependencyRegistry


def __get_existing_annot(
    f, registry: DependencyRegistry = _registry
) -> dict[str, Type]:
    """
    Get the existing annotations in a function.
    """
    existing_annot = {}
    parameters = signature(f).parameters

    for name, parameter in parameters.items():
        if parameter.default != parameter.empty:
            continue

        if registry.has(parameter.annotation):
            existing_annot[name] = parameter.annotation

    return existing_annot


def inject(_func=None, *, registry: DependencyRegistry = _registry):
    """
    Decorator to inject dependencies into a function.

    Parameters:
        registry (DependencyRegistry): the registry used to inject the dependencies. Defaults to module registry.
    """

    def decorated(func):
        @wraps(func)
        def subdecorator(*args, **kwargs):
            for name, annotation in __get_existing_annot(
                func, registry
            ).items():
                if name not in kwargs:  # Only inject if not already provided
                    kwargs[name] = registry.resolve(annotation)
            return func(*args, **kwargs)

        return subdecorator

    if _func is None:
        return decorated

    else:
        return decorated(_func)


def injectable(
    _func: Optional[Type] = None,
    *,
    patch: Optional[Type] = None,
    cached=False,
    autowire=True,
    registry: DependencyRegistry = _registry,
):
    """
    Decorator to register a class as an injectable dependency.

    Parameters:
        patch (Type): The type to patch.
        cached (bool): Whether the dependency should be cached.
    """

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


class_type = TypeVar("class_type", bound=type)


def injected(
    class_: Optional[class_type] = None,
    *,
    validate: bool = True,
    registry: DependencyRegistry = _registry,
) -> Union[class_type, Callable[[class_type], class_type]]:
    """
    Decorator to create default constructor of a class it none present
    """
    if class_ is None:
        return partial(injected, registry=registry, validate=validate)
    if "__init__" in class_.__dict__:
        return class_
    annotations = tuple(class_.__annotations__.items())

    def __init__(self, *args, **kwargs):
        annotations_iter = iter(annotations)
        for arg, (field_name, field_type) in zip(args, annotations_iter):
            if validate and not isinstance(arg, field_type):
                raise TypeError(
                    f"Expected {field_type} for {field_name}, got {type(arg)}"
                )
            setattr(self, field_name, arg)
        missing_args = set(field_name for field_name, _ in annotations_iter)
        kwargs_copy = kwargs.copy()
        for field_name, value in tuple(kwargs_copy.items()):
            if field_name not in class_.__annotations__:
                raise TypeError(
                    f"Keyword argument: {field_name} not found in class {class_.__name__}"
                )
            if field_name not in missing_args:
                raise TypeError(
                    f"Keyword argument: {field_name} already provided as a positional argument"
                )
            field_type = class_.__annotations__[field_name]
            if validate and not isinstance(value, field_type):
                raise TypeError(
                    f"Expected {field_type} for {field_name}, got {type(value)}"
                )
            setattr(self, field_name, value)
            missing_args.remove(field_name)
        for field_name in tuple(missing_args):
            if hasattr(class_, field_name):
                setattr(self, field_name, getattr(class_, field_name))
                missing_args.remove(field_name)
        if missing_args:
            raise TypeError(f"Missing arguments: {', '.join(missing_args)}")

    __init__.__annotations__ = class_.__annotations__.copy()
    __init__.__signature__ = Signature(
        (Parameter("self", Parameter.POSITIONAL_OR_KEYWORD),)
        + tuple(
            Parameter(
                name, Parameter.POSITIONAL_OR_KEYWORD, annotation=annotation
            )
            for name, annotation in __init__.__annotations__.items()
        )
    )
    class_.__init__ = inject(__init__, registry=registry)
    return class_


def wired(
    class_: Optional[class_type] = None,
    *,
    patch=None,
    cached=False,
    autowire=True,
    validate: bool = True,
    registry: DependencyRegistry = _registry,
) -> Union[class_type, Callable[[class_type], class_type]]:
    """
    Decorator that combines @injectable and @injected decorators.
    Registers a class as injectable and auto-generates constructor with dependency injection.
    """
    if class_ is None:
        return partial(
            wired,
            patch=patch,
            cached=cached,
            autowire=autowire,
            validate=validate,
            registry=registry,
        )
    return injectable(
        injected(class_, validate=validate, registry=registry),
        patch=patch,
        cached=cached,
        autowire=autowire,
        registry=registry,
    )

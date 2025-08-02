from functools import partial
from typing import Callable
from typing import Optional
from typing import TypeVar
from typing import Union

from dependify.context import default_registry
from dependify.dependency_registry import DependencyRegistry

from ._injectable import injectable
from ._injected import injected

class_type = TypeVar("class_type", bound=type)


def wired(
    class_: Optional[class_type] = None,
    *,
    patch=None,
    cached=False,
    autowire=True,
    validate: bool = True,
    registry: DependencyRegistry = default_registry,
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

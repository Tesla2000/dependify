from functools import partial
from typing import Callable
from typing import Optional
from typing import TypeVar
from typing import Union

from dependify.context import registry
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
    registry_: DependencyRegistry = registry,
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
            registry=registry_,
        )
    return injectable(
        injected(class_, validate=validate, registry_=registry_),
        patch=patch,
        cached=cached,
        autowire=autowire,
        registry_=registry_,
    )

from functools import partial
from typing import Callable
from typing import Optional
from typing import TypeVar
from typing import Union

from dependify._default_container import default_container
from dependify._dependency_container import DependencyInjectionContainer

from ._injectable import injectable
from ._injected import EvaluationStrategy
from ._injected import injected

class_type = TypeVar("class_type", bound=type)


def wired(
    class_: Optional[class_type] = None,
    *,
    patch=None,
    cached=False,
    autowire=True,
    validate: bool = True,
    evaluation_strategy: EvaluationStrategy = EvaluationStrategy.EAGER,
    container: DependencyInjectionContainer = default_container,
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
            evaluation_strategy=evaluation_strategy,
            container=container,
        )
    return injectable(
        injected(
            class_,
            validate=validate,
            evaluation_strategy=evaluation_strategy,
            container=container,
        ),
        patch=patch,
        cached=cached,
        autowire=autowire,
        container=container,
    )

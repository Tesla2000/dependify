from functools import partial
from typing import Callable
from typing import Optional
from typing import TypeVar
from typing import Union

from dependify._default_container import default_container
from dependify._dependency_container import DependencyInjectionContainer

from ._create_eager import create_eager
from ._create_lazy import create_lazy
from ._evaluation_strategy import EvaluationStrategy

class_type = TypeVar("class_type", bound=type)


def injected(
    class_: Optional[class_type] = None,
    *,
    validate: bool = True,
    evaluation_strategy: EvaluationStrategy = EvaluationStrategy.EAGER,
    container: DependencyInjectionContainer = default_container,
) -> Union[class_type, Callable[[class_type], class_type]]:
    """
    Decorator to create default constructor of a class it none present
    """
    if class_ is None:
        return partial(
            injected,
            container=container,
            validate=validate,
            evaluation_strategy=evaluation_strategy,
        )

    if evaluation_strategy == EvaluationStrategy.EAGER:
        return create_eager(class_, validate, container)
    if evaluation_strategy == EvaluationStrategy.LAZY:
        return create_lazy(class_, validate, container)

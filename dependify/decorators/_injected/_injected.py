from typing import Any
from typing import Optional
from typing import TypeVar

from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)
from typing_extensions import overload
from typing_extensions import Self

from ._evaluation_strategy import EvaluationStrategy
from .creators import EagerCreator
from .creators import LazyCreator
from .creators import OptionalLazyCreator

ClassType = TypeVar("ClassType", bound=type)


class Injected:
    """
    Decorator to create default constructor of a class if none present
    """

    def __init__(
        self,
        container: DependencyInjectionContainer,
        validate: bool = True,
        evaluation_strategy: EvaluationStrategy = EvaluationStrategy.EAGER,
    ):
        self.container = container
        self.validate = validate
        self.evaluation_strategy = evaluation_strategy

    @overload
    def __call__(
        self,
        _func: ClassType,
    ) -> ClassType: ...

    @overload
    def __call__(
        self,
        _func: None = None,
        *,
        validate: Optional[bool] = None,
        evaluation_strategy: Optional[EvaluationStrategy] = None,
    ) -> Self: ...

    def __call__(
        self,
        _func: Optional[ClassType] = None,
        *,
        validate: Optional[bool] = None,
        evaluation_strategy: Optional[EvaluationStrategy] = None,
    ) -> Any:
        def decorator(class_: ClassType) -> ClassType:
            # Use call parameters if provided, otherwise use instance defaults
            actual_validate = (
                validate if validate is not None else self.validate
            )
            actual_strategy = (
                evaluation_strategy
                if evaluation_strategy is not None
                else self.evaluation_strategy
            )

            if not isinstance(actual_strategy, EvaluationStrategy):
                raise ValueError(
                    f"{actual_strategy=} must be an instance of {EvaluationStrategy}"
                )
            if actual_strategy == EvaluationStrategy.EAGER:
                return EagerCreator[class_].create(
                    class_, actual_validate, self.container
                )
            if actual_strategy == EvaluationStrategy.LAZY:
                return LazyCreator[class_].create(
                    class_, actual_validate, self.container
                )
            if actual_strategy == EvaluationStrategy.OPTIONAL_LAZY:
                return OptionalLazyCreator[class_].create(
                    class_, actual_validate, self.container
                )
            raise NotImplementedError(
                f"Evaluation strategy {actual_strategy} not implemented"
            )

        if _func is None:
            return decorator
        else:
            return decorator(_func)

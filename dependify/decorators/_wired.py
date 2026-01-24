from typing import Any
from typing import Optional
from typing import Type
from typing import TypeVar

from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)
from typing_extensions import overload
from typing_extensions import Self

from ._injectable import Injectable
from ._injected import EvaluationStrategy
from ._injected import Injected

ClassType = TypeVar("ClassType", bound=type)


class Wired:
    """
    Decorator that combines @injectable and @injected decorators.
    Registers a class as injectable and auto-generates constructor with dependency injection.
    """

    def __init__(
        self,
        container: DependencyInjectionContainer,
        patch: Optional[Type] = None,
        cached: bool = False,
        autowire: bool = True,
        validate: bool = True,
        evaluation_strategy: EvaluationStrategy = EvaluationStrategy.EAGER,
    ):
        self.container = container
        self.patch = patch
        self.cached = cached
        self.autowire = autowire
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
        patch: Optional[Type] = None,
        cached: Optional[bool] = None,
        autowire: Optional[bool] = None,
        validate: Optional[bool] = None,
        evaluation_strategy: Optional[EvaluationStrategy] = None,
    ) -> Self: ...

    def __call__(
        self,
        _func: Optional[ClassType] = None,
        *,
        patch: Optional[Type] = None,
        cached: Optional[bool] = None,
        autowire: Optional[bool] = None,
        validate: Optional[bool] = None,
        evaluation_strategy: Optional[EvaluationStrategy] = None,
    ) -> Any:
        def decorator(class_: ClassType) -> ClassType:
            # Use call parameters if provided, otherwise use instance defaults
            actual_patch = patch if patch is not None else self.patch
            actual_cached = cached if cached is not None else self.cached
            actual_autowire = (
                autowire if autowire is not None else self.autowire
            )
            actual_validate = (
                validate if validate is not None else self.validate
            )
            actual_strategy = (
                evaluation_strategy
                if evaluation_strategy is not None
                else self.evaluation_strategy
            )

            injected_decorator = Injected(
                self.container,
                validate=actual_validate,
                evaluation_strategy=actual_strategy,
            )
            injectable_decorator = Injectable(
                self.container,
                patch=actual_patch,
                cached=actual_cached,
                autowire=actual_autowire,
            )
            return injectable_decorator(injected_decorator(class_))

        if _func is None:
            return decorator
        else:
            return decorator(_func)

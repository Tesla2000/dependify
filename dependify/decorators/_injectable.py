from typing import Any
from typing import Optional
from typing import Type
from typing import TypeVar

from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)
from typing_extensions import overload
from typing_extensions import Self

ClassType = TypeVar("ClassType", bound=type)


class Injectable:
    def __init__(
        self,
        container: DependencyInjectionContainer,
        patch: Optional[Type] = None,
        cached: bool = False,
        autowire: bool = True,
    ):
        self.container = container
        self.patch = patch
        self.cached = cached
        self.autowire = autowire

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
    ) -> Self: ...

    def __call__(
        self,
        _func: Optional[ClassType] = None,
        *,
        patch: Optional[Type] = None,
        cached: Optional[bool] = None,
        autowire: Optional[bool] = None,
    ) -> Any:
        def decorator(func):
            # Use call parameters if provided, otherwise use instance defaults
            actual_patch = patch if patch is not None else self.patch
            actual_cached = cached if cached is not None else self.cached
            actual_autowire = (
                autowire if autowire is not None else self.autowire
            )

            if actual_patch:
                self.container.register(
                    actual_patch,
                    func,
                    cached=actual_cached,
                    autowired=actual_autowire,
                )
            else:
                self.container.register(
                    func,
                    cached=actual_cached,
                    autowired=actual_autowire,
                )

            return func

        if _func is None:
            return decorator
        else:
            return decorator(_func)

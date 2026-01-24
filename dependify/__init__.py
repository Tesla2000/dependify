"""
Dependify is a package for dependency injection in Python.

Usage:
```python
from dependify import inject, injectable, register

# Decorator registration
@injectable
class A:
    pass

@injectable
class B:
    pass

class C:
    @inject
    def __init__(self, a: A, b: B):
        self.a = a
        self.b = b

C() # No need to pass in A and B since they are injected automatically

# Declarative register of dependencies
register(A)
register(B)

C() # No need to pass in A and B since they are injected automatically
```
"""

from dependify._class_decorator import ClassDecorator
from dependify._conditional_result import ConditionalResult
from dependify._dependency import Dependency
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)
from dependify._dependency_injection_container import NO_TARGET
from dependify.decorators import Eager
from dependify.decorators import Excluded
from dependify.decorators import Inject
from dependify.decorators import Injectable
from dependify.decorators import Injected
from dependify.decorators import Lazy
from dependify.decorators import OptionalLazy
from dependify.decorators import Wired

__all__ = [
    "ClassDecorator",
    "ConditionalResult",
    "Dependency",
    "DependencyInjectionContainer",
    "Eager",
    "Excluded",
    "Inject",
    "Injectable",
    "Injected",
    "Lazy",
    "NO_TARGET",
    "OptionalLazy",
    "Wired",
]

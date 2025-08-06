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

from dependify._conditional_result import ConditionalResult
from dependify._default_registry import default_registry
from dependify._default_registry import dependencies
from dependify._default_registry import has
from dependify._default_registry import register
from dependify._default_registry import register_dependency
from dependify._default_registry import resolve
from dependify._dependency import Dependency
from dependify._dependency_registry import DependencyRegistry
from dependify.decorators import inject
from dependify.decorators import injectable
from dependify.decorators import injected
from dependify.decorators import wired

__all__ = [
    "Dependency",
    "DependencyRegistry",
    "inject",
    "injectable",
    "injected",
    "wired",
    "register",
    "register_dependency",
    "resolve",
    "has",
    "dependencies",
    "default_registry",
    "ConditionalResult",
]

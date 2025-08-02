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
from dependify._dependency import Dependency
from dependify.context import default_registry
from dependify.context import dependencies
from dependify.context import has
from dependify.context import register
from dependify.context import register_dependency
from dependify.context import resolve
from dependify.decorators import inject
from dependify.decorators import injectable
from dependify.decorators import injected
from dependify.decorators import wired
from dependify.dependency_registry import DependencyRegistry

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
    "dependency_registry",
    "default_registry",
    "ConditionalResult",
]

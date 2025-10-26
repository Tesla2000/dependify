"""
Markers for field-level lazy evaluation annotations.

Usage:
    from typing import Annotated
    from dependify import Lazy, OptionalLazy

    @injected
    class Service:
        # This field will be lazily evaluated even if class uses EAGER strategy
        db: Annotated[Database, Lazy]

        # This field will be lazily evaluated and returns None if not registered
        cache: Annotated[Cache, OptionalLazy]
"""


class _LazyMarker:
    """
    Marker class for lazy field evaluation.

    When used with Annotated, marks a field for lazy evaluation regardless of
    the class-level evaluation strategy.

    Example:
        @injected  # defaults to EAGER
        class Service:
            db: Annotated[Database, Lazy]  # This field is lazy
            logger: Logger  # This field is eager
    """

    def __repr__(self) -> str:
        return "Lazy"

    def __eq__(self, other) -> bool:
        return isinstance(other, _LazyMarker)

    def __hash__(self) -> int:
        return hash("Lazy")


class _OptionalLazyMarker:
    """
    Marker class for optional lazy field evaluation.

    When used with Annotated, marks a field for lazy evaluation that returns None
    if the dependency is not registered, rather than raising an error.

    Example:
        @injected
        class Service:
            cache: Annotated[Cache, OptionalLazy]  # Returns None if Cache not registered
    """

    def __repr__(self) -> str:
        return "OptionalLazy"

    def __eq__(self, other) -> bool:
        return isinstance(other, _OptionalLazyMarker)

    def __hash__(self) -> int:
        return hash("OptionalLazy")


# Singleton instances to be used as markers
Lazy = _LazyMarker()
OptionalLazy = _OptionalLazyMarker()

from typing import Any
from typing import Callable
from typing import Sequence
from typing import Tuple


class ConditionalResult:
    """
    A conditional dependency resolver that returns different values based on the class
    receiving the injection.

    This allows you to inject different dependency instances based on the type of the
    class being instantiated, enabling context-aware dependency injection.

    Args:
        default: The default value to return if no conditions match
        conditions: A sequence of tuples, each containing:
            - A callable that takes a class (not instance) and returns a boolean
            - The value to return if the condition is True

    Example:
        >>> container.register(
        ...     Logger,
        ...     lambda: ConditionalResult(
        ...         Logger("INFO"),  # Default
        ...         (
        ...             (lambda cls: issubclass(cls, AdminService), Logger("ERROR")),
        ...             (lambda cls: issubclass(cls, UserService), Logger("DEBUG")),
        ...         )
        ...     )
        ... )

    Note:
        The condition callable receives a class (type), not an instance. Use issubclass()
        or type comparisons, not isinstance().
    """

    def __init__(
        self,
        default: Any,
        conditions: Sequence[Tuple[Callable[[type], bool], Any]] = (),
    ):
        self.default = default
        self.conditions = conditions

    def resolve(self, instance: Any) -> Any:
        """
        Resolve the conditional result based on the instance's class.

        Args:
            instance: The instance being constructed (will be converted to its type)

        Returns:
            The value from the first matching condition, or the default value
        """
        type_ = instance
        if not isinstance(type_, type):
            type_ = type(type_)
        for condition, value in self.conditions:
            if condition(type_):
                return value
        return self.default

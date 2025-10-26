from typing import Any


def validate_arg(
    validate: bool, field_type: Any, value: Any, field_name: str
) -> None:
    if (
        validate
        and isinstance(field_type, type)
        and not isinstance(value, field_type)
    ):
        raise TypeError(
            f"Expected {field_type} for {field_name}, got {type(value)}"
        )

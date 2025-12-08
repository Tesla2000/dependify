from typing import Annotated
from typing import Any
from typing import get_args
from typing import get_origin

from ._protocol_translator import (
    translate_protocol,
)


def validate_arg(
    validate: bool, field_type: Any, value: Any, field_name: str
) -> None:
    field_type = translate_protocol(field_type)
    validated_type = field_type
    if get_origin(field_type) is Annotated:
        args = get_args(field_type)
        if args:
            validated_type = args[0]
    if (
        validate
        and isinstance(validated_type, type)
        and not isinstance(value, validated_type)
    ):
        raise TypeError(
            f"Expected {validated_type} for {field_name}, got {type(value)}"
        )

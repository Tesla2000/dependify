from typing import Annotated
from typing import ClassVar
from typing import get_args
from typing import get_origin


def is_class_var(type_hint) -> bool:
    origin, args = get_origin(type_hint), get_args(type_hint)
    if not origin or not args:
        return False
    if origin is ClassVar:
        return True
    if origin is Annotated:
        return any(map(is_class_var, args))
    return False

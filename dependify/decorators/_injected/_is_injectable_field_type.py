from typing import Annotated
from typing import Any
from typing import get_args
from typing import get_origin
from typing import Union


def is_injectable_field_type(annotation: Any) -> bool:
    """Return True if *annotation* represents a custom type suitable for DI.

    The intent is to guard against adding injection decorators / lazy
    properties to fields whose types can never come from the container:

    * Builtin primitives (``int``, ``str``, ``bool``, ``float``, …) — any type
      whose ``__module__`` is ``"builtins"``.
    * Generic collection aliases (``list[str]``, ``dict[str, int]``,
      ``Literal["x"]``, …) — anything with a non-``None`` ``get_origin()``
      that is not ``Union`` or ``Annotated``.

    The following are **still** treated as injectable:

    * **Subclasses of builtins** (e.g. ``class Integer(int)``) — their module
      is the user's module, not ``"builtins"``.
    * **``Optional[CustomType]``** / ``Union[CustomType, ...]`` — the check
      recurses into the union args; True if *any* arg is injectable.
    * **``Annotated[CustomType, ...]``** — unwrapped transparently.
    """
    origin = get_origin(annotation)
    if origin is Annotated:
        args = get_args(annotation)
        return is_injectable_field_type(args[0]) if args else False
    if origin is Union:
        return any(
            is_injectable_field_type(arg) for arg in get_args(annotation)
        )
    if origin is not None:
        # Covers list[], dict[], Literal[], etc.
        return False
    if not isinstance(annotation, type):
        return False
    return annotation.__module__ != "builtins"

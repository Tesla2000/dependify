from abc import ABC
from typing import Annotated
from typing import Any
from typing import Dict
from typing import get_args
from typing import get_origin
from typing import Type
from typing import TypeVar
from typing import Union

from dependify._conditional_result import ConditionalResult
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)
from dependify._dependency_injection_container import NO_TARGET
from pydantic import BaseModel
from pydantic import field_validator
from pydantic import model_validator
from pydantic import ModelWrapValidatorHandler
from typing_extensions import Self

from ._markers import Excluded
from ._protocol_translator import (
    translate_protocol,
)
from ._validate_arg import validate_arg

ClassType = TypeVar("ClassType", bound=BaseModel)


def _is_injectable_field_type(annotation: Any) -> bool:
    """Return True if the annotation is a custom type suitable for injection.

    Excludes builtin types (int, str, bool, etc.) and collection generics
    (list[], dict[], Literal[], etc.), but recurses into Union/Optional so
    that ``Optional[CustomType]`` is still treated as injectable.  Subclasses
    of builtins (e.g. ``class Integer(int)``) are also included.
    """
    origin = get_origin(annotation)
    if origin is Annotated:
        args = get_args(annotation)
        return _is_injectable_field_type(args[0]) if args else False
    if origin is Union:
        return any(
            _is_injectable_field_type(arg) for arg in get_args(annotation)
        )
    if origin is not None:
        return False
    if not isinstance(annotation, type):
        return False
    return annotation.__module__ != "builtins"


def create_pydantic_wrap_validator(
    class_: Type[ClassType],
    validate: bool,
    container: DependencyInjectionContainer,
    class_annotations: Dict[str, Any],
) -> Type[ClassType]:
    annotations = tuple(class_annotations.items())

    def _resolve_conditional(cls, value: Any) -> Any:
        if isinstance(value, ConditionalResult):
            return value.resolve(cls)
        return value

    def __eq__(self, other: Any) -> bool:
        if "__eq__" in class_.__dict__:
            return class_.__eq__(self, other)
        if not isinstance(other, class_):
            return False
        return (
            self.__dict__ == other.__dict__
            and getattr(self, "__pydantic_extra__", None)
            == getattr(other, "__pydantic_extra__", None)
            and getattr(self, "__pydantic_private__", None)
            == getattr(other, "__pydantic_private__", None)
        )

    def _inject_fields(
        cls: Type[BaseModel],
        data: Any,
        handler: ModelWrapValidatorHandler[Self],
    ) -> Self:
        model_fields = cls.model_fields
        if isinstance(data, dict):
            data_to_validate = {
                **{
                    field_name: resolved_value
                    for field_name, resolved_value in zip(
                        model_fields.keys(),
                        (
                            container.resolve_optional(
                                field_info.annotation, NO_TARGET
                            )
                            for field_info in model_fields.values()
                        ),
                    )
                    if resolved_value is not NO_TARGET
                },
                **data,
            }
        else:
            data_to_validate = data
        validated_object = handler(data_to_validate)
        for field_name, field_type in annotations:
            if getattr(field_type, "_is_protocol", False) and not getattr(
                field_type, "_is_runtime_protocol", True
            ):
                field_type = translate_protocol(field_type)
            resolution_result = container.resolve_optional(
                field_type, NO_TARGET
            )
            if field_name in model_fields or resolution_result is NO_TARGET:
                continue
            validate_arg(validate, field_type, resolution_result, field_name)
            setattr(validated_object, field_name, resolution_result)
        return validated_object

    validated_fields = tuple(
        field_name
        for field_name, field_info in class_.model_fields.items()
        if Excluded not in (field_info.metadata or ())
        and _is_injectable_field_type(field_info.annotation)
    )
    _base_meta = type(class_)

    class _InjectableMeta(_base_meta):
        def __instancecheck__(cls, instance):
            return type(instance) is class_ or _base_meta.__instancecheck__(
                cls, instance
            )

        def __subclasscheck__(cls, subclass):
            return subclass is class_ or _base_meta.__subclasscheck__(
                cls, subclass
            )

    injectable_class = _InjectableMeta(
        class_.__name__,
        (
            (
                class_,
                ABC,
            )
            if ABC in class_.__bases__
            else (class_,)
        ),
        {
            _inject_fields.__name__: model_validator(mode="wrap")(
                classmethod(_inject_fields)
            ),
            _resolve_conditional.__name__: (
                field_validator(
                    *validated_fields,
                    mode="before",
                )(classmethod(_resolve_conditional))
                if validated_fields
                else classmethod(_resolve_conditional)
            ),
            "__doc__": class_.__doc__,
            __eq__.__name__: __eq__,
        },
    )

    return injectable_class

from typing import Any
from typing import Dict
from typing import Type
from typing import TypeVar

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

from ._protocol_translator import (
    translate_protocol,
)
from ._validate_arg import validate_arg

ClassType = TypeVar("ClassType", bound=BaseModel)


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

    injectable_class = type(
        class_.__name__,
        (class_,),
        {
            _inject_fields.__name__: model_validator(mode="wrap")(
                classmethod(_inject_fields)
            ),
            _resolve_conditional.__name__: field_validator("*", mode="before")(
                classmethod(_resolve_conditional)
            ),
        },
    )
    injectable_class.__class__ = class_.__class__
    return injectable_class

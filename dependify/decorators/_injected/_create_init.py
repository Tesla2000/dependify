from inspect import Parameter
from inspect import Signature
from typing import Any
from typing import Dict
from typing import TypeVar

from dependify._conditional_result import ConditionalResult
from dependify._dependency_injection_container import (
    DependencyInjectionContainer,
)
from dependify._is_class_var import is_class_var
from dependify.decorators import inject

from ._markers import Lazy
from ._markers import OptionalLazy
from ._protocol_translator import (
    translate_protocol,
)
from ._validate_arg import validate_arg

ClassType = TypeVar("ClassType")


def create_init(
    class_: ClassType,
    validate: bool,
    container: DependencyInjectionContainer,
    class_annotations: Dict[str, Any],
) -> ClassType:
    annotations = tuple(class_annotations.items())

    def __init__(self, *args, **kwargs):
        class_var_annotations = dict(
            (field_name, type_hint)
            for field_name, type_hint in annotations
            if is_class_var(type_hint)
        )
        annotations_iter = iter(
            (field_name, type_hint)
            for field_name, type_hint in annotations
            if not is_class_var(type_hint)
        )
        for arg, (field_name, field_type) in zip(args, annotations_iter):
            validate_arg(validate, field_type, arg, field_name)
            setattr(self, field_name, arg)
        missing_args = set(
            field_name for field_name, type_hint in annotations_iter
        )
        kwargs_copy = kwargs.copy()
        for field_name, value in tuple(kwargs_copy.items()):
            if field_name not in class_annotations:
                raise TypeError(
                    f"Keyword argument: {field_name} not found in class {class_.__name__}"
                )
            if field_name not in missing_args.union(class_var_annotations):
                raise TypeError(
                    f"Keyword argument: {field_name} already provided as a positional argument"
                )
            field_type = class_annotations[field_name]
            if getattr(field_type, "_is_protocol", False) and not getattr(
                field_type, "_is_runtime_protocol", True
            ):
                field_type = translate_protocol(field_type)
            if isinstance(value, ConditionalResult):
                value = value.resolve(self)
            validate_arg(validate, field_type, value, field_name)
            setattr(self, field_name, value)
            missing_args.difference_update((field_name,))
        for field_name in tuple(missing_args):
            if hasattr(class_, field_name):
                if not isinstance(
                    value := getattr(class_, field_name), property
                ):
                    setattr(self, field_name, value)
                missing_args.difference_update((field_name,))
        if missing_args:
            missing_arguments = ", ".join(
                f"{arg_name} of type {class_annotations.get(arg_name, 'unknown')}"
                for arg_name in missing_args
            )
            raise TypeError(
                f"Missing arguments: {missing_arguments} for {type(self).__name__}"
            )
        if hasattr(class_, "__post_init__"):
            class_.__post_init__(self)

    __init__.__annotations__ = class_annotations.copy()
    __init__.__signature__ = Signature(
        (Parameter("self", Parameter.POSITIONAL_OR_KEYWORD),)
        + tuple(
            Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, annotation=a)
            for name, a in class_annotations.items()
            if not any(
                map(
                    (Lazy, OptionalLazy).__contains__,
                    getattr(a, "__metadata__", ()),
                )
            )
        )
    )
    class_.__init__ = inject(__init__, container=container)
    return class_

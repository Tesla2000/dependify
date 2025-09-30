from functools import partial
from inspect import Parameter
from inspect import Signature
from typing import Callable
from typing import Dict
from typing import get_type_hints
from typing import Optional
from typing import runtime_checkable
from typing import Type
from typing import TypeVar
from typing import Union

from dependify._conditional_result import ConditionalResult
from dependify._default_container import default_container
from dependify._dependency_container import DependencyInjectionContainer
from dependify.decorators import inject

from ._get_annotations import get_annotations

class_type = TypeVar("class_type", bound=type)
_protocol_translator: Dict[Type, Type] = {}


def injected(
    class_: Optional[class_type] = None,
    *,
    validate: bool = True,
    container: DependencyInjectionContainer = default_container,
) -> Union[class_type, Callable[[class_type], class_type]]:
    """
    Decorator to create default constructor of a class it none present
    """
    if class_ is None:
        return partial(injected, container=container, validate=validate)
    if "__init__" in class_.__dict__:
        prev_init = class_.__init__

        def __init__(self, *args, **kwargs) -> None:
            prev_init(self, *args, **kwargs)
            if hasattr(self, "__post_init__"):
                self.__post_init__()

        class_.__init__ = __init__
        return class_
    try:
        class_annotations = get_type_hints(class_)
    except NameError:
        class_annotations = get_annotations(class_)
    annotations = tuple(class_annotations.items())

    def __init__(self, *args, **kwargs):
        annotations_iter = iter(annotations)
        for arg, (field_name, field_type) in zip(args, annotations_iter):
            if (
                validate
                and isinstance(field_type, type)
                and not isinstance(arg, field_type)
            ):
                raise TypeError(
                    f"Expected {field_type} for {field_name}, got {type(arg)}"
                )
            setattr(self, field_name, arg)
        missing_args = set(field_name for field_name, _ in annotations_iter)
        kwargs_copy = kwargs.copy()
        for field_name, value in tuple(kwargs_copy.items()):
            if field_name not in class_annotations:
                raise TypeError(
                    f"Keyword argument: {field_name} not found in class {class_.__name__}"
                )
            if field_name not in missing_args:
                raise TypeError(
                    f"Keyword argument: {field_name} already provided as a positional argument"
                )
            field_type = class_annotations[field_name]
            if getattr(field_type, "_is_protocol", False) and not getattr(
                field_type, "_is_runtime_protocol", True
            ):
                _protocol_translator[field_type] = _protocol_translator.get(
                    field_type, runtime_checkable(field_type)
                )
                field_type = _protocol_translator[field_type]
            if isinstance(value, ConditionalResult):
                value = value.resolve(self)
            if (
                validate
                and isinstance(field_type, type)
                and not isinstance(value, field_type)
            ):
                raise TypeError(
                    f"Expected {field_type} for {field_name}, got {type(value)}"
                )
            setattr(self, field_name, value)
            missing_args.remove(field_name)
        for field_name in tuple(missing_args):
            if hasattr(class_, field_name):
                setattr(self, field_name, getattr(class_, field_name))
                missing_args.remove(field_name)
        if missing_args:
            missing_arguments = ", ".join(
                f"{arg_name} of type {class_annotations.get(arg_name, 'unknown')}"
                for arg_name in missing_args
            )
            raise TypeError(
                f"Missing arguments: {missing_arguments} for {type(self).__name__}"
            )
        if hasattr(self, "__post_init__"):
            self.__post_init__()

    __init__.__annotations__ = class_annotations.copy()
    __init__.__signature__ = Signature(
        (Parameter("self", Parameter.POSITIONAL_OR_KEYWORD),)
        + tuple(
            Parameter(
                name, Parameter.POSITIONAL_OR_KEYWORD, annotation=annotation
            )
            for name, annotation in __init__.__annotations__.items()
        )
    )
    class_.__init__ = inject(__init__, container=container)
    return class_

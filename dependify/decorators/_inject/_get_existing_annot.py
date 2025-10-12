from inspect import signature
from typing import Dict
from typing import get_origin
from typing import Type

from dependify._default_container import default_container
from dependify._dependency_container import DependencyInjectionContainer


def get_existing_annot(
    f, container: DependencyInjectionContainer = default_container
) -> Dict[str, Type]:
    """
    Get the existing annotations in a function.
    """
    existing_annot = {}
    parameters = signature(f).parameters

    for name, parameter in parameters.items():
        if parameter.default != parameter.empty:
            continue

        annotation = parameter.annotation
        if annotation in container:
            existing_annot[name] = annotation
        else:
            # Check if it's a generic type - we can try to resolve it
            origin = get_origin(annotation)
            if origin is not None:
                existing_annot[name] = annotation

    return existing_annot

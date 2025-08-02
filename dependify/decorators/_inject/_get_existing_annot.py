from inspect import signature
from typing import Dict
from typing import Type

from dependify.context import registry
from dependify.dependency_registry import DependencyRegistry


def get_existing_annot(
    f, registry_: DependencyRegistry = registry
) -> Dict[str, Type]:
    """
    Get the existing annotations in a function.
    """
    existing_annot = {}
    parameters = signature(f).parameters

    for name, parameter in parameters.items():
        if parameter.default != parameter.empty:
            continue

        if registry_.has(parameter.annotation):
            existing_annot[name] = parameter.annotation

    return existing_annot

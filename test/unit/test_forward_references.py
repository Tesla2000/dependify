from __future__ import annotations

import unittest

from dependify import DependencyInjectionContainer
from dependify import Wired

# Module-level container for module-level decorators
_container = DependencyInjectionContainer()
wired = Wired(_container)


@wired
class Foo:
    """Must be non-local for it to work"""


class TestForwardReferences(unittest.TestCase):
    def test_forward_reference(self):
        @wired
        class Bar:
            foo: "Foo"

        self.assertIsInstance(Bar().foo, Foo)

    def test_future_annotations(self):
        @wired
        class Bar:
            foo: Foo

        self.assertIsInstance(Bar().foo, Foo)

from unittest import TestCase

from dependify import DependencyRegistry


class TestContext(TestCase):

    def test_context(self):
        class A:
            pass

        registry = DependencyRegistry()
        registry.register(A)

        class B:
            pass

        with registry:
            registry.register(B)
            self.assertIn(B, registry)
            self.assertTrue(hasattr(registry, "_dep_cp"))
        self.assertNotIn(B, registry)
        self.assertFalse(hasattr(registry, "_dep_cp"))

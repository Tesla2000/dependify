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

        class C:
            pass

        self.assertIn(A, registry)
        with registry:
            registry.register(B)
            self.assertIn(A, registry)
            self.assertIn(B, registry)
            self.assertNotIn(C, registry)
            self.assertEqual(1, len(registry._dep_cp))
            with registry:
                registry.register(C)
                self.assertIn(A, registry)
                self.assertIn(B, registry)
                self.assertIn(C, registry)
                self.assertEqual(2, len(registry._dep_cp))
            self.assertEqual(1, len(registry._dep_cp))
            self.assertIn(A, registry)
            self.assertIn(B, registry)
            self.assertNotIn(C, registry)

        self.assertNotIn(B, registry)
        self.assertFalse(registry._dep_cp)

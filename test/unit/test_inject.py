from unittest import TestCase

from dependify import inject


class TestInject(TestCase):

    def test_inject_with_registry(self):
        """
        Test if the `inject` decorator can be used with a custom registry.
        """
        from dependify import DependencyRegistry

        class A:
            pass

        registry = DependencyRegistry()
        registry.register(A)

        @inject(registry=registry)
        def test(a: A):
            self.assertIsInstance(a, A)

        test()

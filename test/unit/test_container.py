from unittest import TestCase

from src.dependify import DependencyRegistry


class TestContainer(TestCase):

    def test_registry_register_class(self):
        """
        Test if a class dependency can be registered successfully.
        """

        class A:
            pass

        registry = DependencyRegistry()
        registry.register(A)
        self.assertTrue(registry.has(A))

    def test_registry_register_function(self):
        """
        Test if a function based dependency can be registered successfully.
        """
        registry = DependencyRegistry()

        class A:
            pass

        def func():
            return A()

        registry.register(A, func)
        self.assertTrue(registry.has(A))

    def test_registry_resolve(self):
        """
        Test if a dependency can be resolved successfully.
        """

        class A:
            pass

        registry = DependencyRegistry()
        registry.register(A)
        result = registry.resolve(A)
        self.assertIsInstance(result, A)

    def test_registry_resolve_cached(self):
        """
        Test if the dependency is cached when the `cached` property is set to `True`.
        """

        class A:
            pass

        registry = DependencyRegistry()
        registry.register(A, cached=True)
        result1 = registry.resolve(A)
        result2 = registry.resolve(A)
        self.assertIs(result1, result2)

    def test_registry_resolve_not_cached(self):
        """
        Test if the dependency is not cached when the `cached` property is set to `False`.
        """

        class A:
            pass

        registry = DependencyRegistry()
        registry.register(A, cached=False)
        result1 = registry.resolve(A)
        result2 = registry.resolve(A)
        self.assertIsNot(result1, result2)

    def test_registry_resolve_not_cached_by_default(self):
        """
        Test if the dependency is not cached by default.
        """

        class A:
            pass

        registry = DependencyRegistry()
        registry.register(A)
        result1 = registry.resolve(A)
        result2 = registry.resolve(A)
        self.assertIsNot(result1, result2)

    def test_registry_resolve_with_dependencies(self):
        """
        Test if a dependency can be resolved successfully with dependencies.
        """

        class B:
            pass

        class A:
            def __init__(self, b: B):
                self.b = b

        registry = DependencyRegistry()
        registry.register(A)
        registry.register(B)
        result = registry.resolve(A)
        self.assertIsInstance(result, A)
        self.assertIsInstance(result.b, B)

    def test_registry_resolve_autowire_dependency_disabled(self):
        """
        Test if a dependency can be resolved successfully with autowire disabled.
        """

        class B:
            pass

        class A:
            def __init__(self, b: B):
                self.b = b

        registry = DependencyRegistry()
        registry.register(A, autowired=False)
        registry.register(B)

        with self.assertRaisesRegex(
            TypeError, "missing 1 required positional argument"
        ):
            registry.resolve(A)

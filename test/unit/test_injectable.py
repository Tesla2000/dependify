from unittest import TestCase

from dependify import DependencyRegistry
from dependify import has
from dependify import injectable
from dependify import resolve


class TestInjectable(TestCase):

    def test_injectable_with_custom_registry(self):
        """Test @injectable with a custom registry"""
        registry = DependencyRegistry()

        @injectable(registry=registry)
        class A:
            pass

        # Should be registered in custom registry
        self.assertTrue(registry.has(A))
        # Should not be in default registry
        self.assertFalse(has(A))
        # Should resolve correctly
        instance = registry.resolve(A)
        self.assertIsInstance(instance, A)

    def test_injectable_with_default_registry(self):
        """Test @injectable using default registry"""

        @injectable
        class B:
            pass

        # Should be registered in default registry
        self.assertTrue(has(B))
        # Should resolve correctly
        instance = resolve(B)
        self.assertIsInstance(instance, B)

    def test_injectable_with_patch_parameter(self):
        """Test @injectable with patch parameter to replace existing class"""
        registry = DependencyRegistry()

        class Original:
            def method(self):
                return "original"

        # Register original
        registry.register(Original)

        @injectable(patch=Original, registry=registry)
        class Patched:
            def method(self):
                return "patched"

        # Should resolve to patched version
        instance = registry.resolve(Original)
        self.assertIsInstance(instance, Patched)
        self.assertEqual(instance.method(), "patched")

    def test_injectable_with_cached_true(self):
        """Test @injectable with cached=True (singleton behavior)"""
        registry = DependencyRegistry()

        @injectable(cached=True, registry=registry)
        class CachedService:
            pass

        # Multiple resolves should return same instance
        instance1 = registry.resolve(CachedService)
        instance2 = registry.resolve(CachedService)
        self.assertIs(instance1, instance2)

    def test_injectable_with_cached_false(self):
        """Test @injectable with cached=False (new instance each time)"""
        registry = DependencyRegistry()

        @injectable(cached=False, registry=registry)
        class NonCachedService:
            pass

        # Multiple resolves should return different instances
        instance1 = registry.resolve(NonCachedService)
        instance2 = registry.resolve(NonCachedService)
        self.assertIsNot(instance1, instance2)

    def test_injectable_with_autowire_false(self):
        """Test @injectable with autowire=False"""
        registry = DependencyRegistry()

        @injectable(registry=registry)
        class Dependency:
            pass

        @injectable(autowire=False, registry=registry)
        class ServiceNoAutowire:
            def __init__(self, dep: Dependency):
                self.dep = dep

        # Should raise error when resolving without manual dependency
        with self.assertRaises(TypeError):
            registry.resolve(ServiceNoAutowire)

    def test_injectable_with_autowire_true(self):
        """Test @injectable with autowire=True (default)"""
        registry = DependencyRegistry()

        @injectable(registry=registry)
        class Dependency:
            pass

        @injectable(autowire=True, registry=registry)
        class ServiceWithAutowire:
            def __init__(self, dep: Dependency):
                self.dep = dep

        # Should autowire dependencies
        instance = registry.resolve(ServiceWithAutowire)
        self.assertIsInstance(instance, ServiceWithAutowire)
        self.assertIsInstance(instance.dep, Dependency)

    def test_injectable_multiple_decorations(self):
        """Test multiple @injectable decorations on different classes"""
        registry = DependencyRegistry()

        @injectable(registry=registry)
        class ServiceA:
            pass

        @injectable(registry=registry)
        class ServiceB:
            def __init__(self, a: ServiceA):
                self.a = a

        @injectable(registry=registry)
        class ServiceC:
            def __init__(self, a: ServiceA, b: ServiceB):
                self.a = a
                self.b = b

        # All should be registered
        self.assertTrue(registry.has(ServiceA))
        self.assertTrue(registry.has(ServiceB))
        self.assertTrue(registry.has(ServiceC))

        # Should resolve with dependencies
        c_instance = registry.resolve(ServiceC)
        self.assertIsInstance(c_instance.a, ServiceA)
        self.assertIsInstance(c_instance.b, ServiceB)
        self.assertIsInstance(c_instance.b.a, ServiceA)

    def test_injectable_with_factory_function(self):
        """Test @injectable on a factory function instead of class"""
        registry = DependencyRegistry()

        class ServiceFromFactory:
            def __init__(self, value):
                self.value = value

        @injectable(registry=registry)
        def service_factory():
            return ServiceFromFactory(42)

        # Factory should be registered
        self.assertTrue(registry.has(service_factory))

        # Should resolve to factory result
        instance = registry.resolve(service_factory)
        self.assertIsInstance(instance, ServiceFromFactory)
        self.assertEqual(instance.value, 42)

    def test_injectable_inheritance(self):
        """Test @injectable with class inheritance"""
        registry = DependencyRegistry()

        @injectable(registry=registry)
        class BaseService:
            def get_name(self):
                return "base"

        @injectable(registry=registry)
        class DerivedService(BaseService):
            def get_name(self):
                return "derived"

        # Both should be registered independently
        base_instance = registry.resolve(BaseService)
        derived_instance = registry.resolve(DerivedService)

        self.assertEqual(base_instance.get_name(), "base")
        self.assertEqual(derived_instance.get_name(), "derived")
        self.assertIsInstance(derived_instance, BaseService)

    def test_injectable_with_all_parameters(self):
        """Test @injectable with all parameters specified"""
        registry = DependencyRegistry()

        class Interface:
            pass

        @injectable(
            patch=Interface, cached=True, autowire=True, registry=registry
        )
        class Implementation(Interface):
            pass

        # Should resolve Interface to Implementation
        instance1 = registry.resolve(Interface)
        instance2 = registry.resolve(Interface)

        self.assertIsInstance(instance1, Implementation)
        # Should be cached (same instance)
        self.assertIs(instance1, instance2)

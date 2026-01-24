from unittest import TestCase

from dependify import DependencyInjectionContainer
from dependify import Injectable


class TestInjectable(TestCase):

    def test_injectable_with_custom_container(self):
        """Test @Injectable with a custom container"""
        container = DependencyInjectionContainer()

        injectable = Injectable(container)

        @injectable
        class A:
            pass

        # Should be registered in custom container
        self.assertTrue(A in container)
        # Should resolve correctly
        instance = container.resolve(A)
        self.assertIsInstance(instance, A)

    def test_injectable_with_default_container(self):
        """Test @Injectable using custom container"""
        container = DependencyInjectionContainer()

        injectable = Injectable(container)

        @injectable
        class B:
            pass

        # Should be registered in container
        self.assertTrue(B in container)
        # Should resolve correctly
        instance = container.resolve(B)
        self.assertIsInstance(instance, B)

    def test_injectable_with_patch_parameter(self):
        """Test @Injectable with patch parameter to replace existing class"""
        container = DependencyInjectionContainer()

        class Original:
            def method(self):
                return "original"

        # Register original
        container.register(Original)

        injectable = Injectable(container, patch=Original)

        @injectable
        class Patched:
            def method(self):
                return "patched"

        # Should resolve to patched version
        instance = container.resolve(Original)
        self.assertIsInstance(instance, Patched)
        self.assertEqual(instance.method(), "patched")

    def test_injectable_with_cached_true(self):
        """Test @Injectable with cached=True (singleton behavior)"""
        container = DependencyInjectionContainer()

        injectable = Injectable(container, cached=True)

        @injectable
        class CachedService:
            pass

        # Multiple resolves should return same instance
        instance1 = container.resolve(CachedService)
        instance2 = container.resolve(CachedService)
        self.assertIs(instance1, instance2)

    def test_injectable_with_cached_false(self):
        """Test @Injectable with cached=False (new instance each time)"""
        container = DependencyInjectionContainer()

        injectable = Injectable(container, cached=False)

        @injectable
        class NonCachedService:
            pass

        # Multiple resolves should return different instances
        instance1 = container.resolve(NonCachedService)
        instance2 = container.resolve(NonCachedService)
        self.assertIsNot(instance1, instance2)

    def test_injectable_with_autowire_false(self):
        """Test @Injectable with autowire=False"""
        container = DependencyInjectionContainer()

        injectable1 = Injectable(container)

        @injectable1
        class Dependency:
            pass

        injectable2 = Injectable(container, autowire=False)

        @injectable2
        class ServiceNoAutowire:
            def __init__(self, dep: Dependency):
                self.dep = dep

        # Should raise error when resolving without manual dependency
        with self.assertRaises(TypeError):
            container.resolve(ServiceNoAutowire)

    def test_injectable_with_autowire_true(self):
        """Test @Injectable with autowire=True (default)"""
        container = DependencyInjectionContainer()

        injectable1 = Injectable(container)

        @injectable1
        class Dependency:
            pass

        injectable2 = Injectable(container, autowire=True)

        @injectable2
        class ServiceWithAutowire:
            def __init__(self, dep: Dependency):
                self.dep = dep

        # Should autowire dependencies
        instance = container.resolve(ServiceWithAutowire)
        self.assertIsInstance(instance, ServiceWithAutowire)
        self.assertIsInstance(instance.dep, Dependency)

    def test_injectable_multiple_decorations(self):
        """Test multiple @Injectable decorations on different classes"""
        container = DependencyInjectionContainer()

        injectable = Injectable(container)

        @injectable
        class ServiceA:
            pass

        @injectable
        class ServiceB:
            def __init__(self, a: ServiceA):
                self.a = a

        @injectable
        class ServiceC:
            def __init__(self, a: ServiceA, b: ServiceB):
                self.a = a
                self.b = b

        # All should be registered
        self.assertTrue(ServiceA in container)
        self.assertTrue(ServiceB in container)
        self.assertTrue(ServiceC in container)

        # Should resolve with dependencies
        c_instance = container.resolve(ServiceC)
        self.assertIsInstance(c_instance.a, ServiceA)
        self.assertIsInstance(c_instance.b, ServiceB)
        self.assertIsInstance(c_instance.b.a, ServiceA)

    def test_injectable_with_factory_function(self):
        """Test @Injectable on a factory function instead of class"""
        container = DependencyInjectionContainer()

        class ServiceFromFactory:
            def __init__(self, value):
                self.value = value

        injectable = Injectable(container)

        @injectable
        def service_factory():
            return ServiceFromFactory(42)

        # Factory should be registered
        self.assertTrue(service_factory in container)

        # Should resolve to factory result
        instance = container.resolve(service_factory)
        self.assertIsInstance(instance, ServiceFromFactory)
        self.assertEqual(instance.value, 42)

    def test_injectable_inheritance(self):
        """Test @Injectable with class inheritance"""
        container = DependencyInjectionContainer()

        injectable = Injectable(container)

        @injectable
        class BaseService:
            def get_name(self):
                return "base"

        @injectable
        class DerivedService(BaseService):
            def get_name(self):
                return "derived"

        # Both should be registered independently
        base_instance = container.resolve(BaseService)
        derived_instance = container.resolve(DerivedService)

        self.assertEqual(base_instance.get_name(), "base")
        self.assertEqual(derived_instance.get_name(), "derived")
        self.assertIsInstance(derived_instance, BaseService)

    def test_injectable_with_all_parameters(self):
        """Test @Injectable with all parameters specified"""
        container = DependencyInjectionContainer()

        class Interface:
            pass

        injectable = Injectable(
            container, patch=Interface, cached=True, autowire=True
        )

        @injectable
        class Implementation(Interface):
            pass

        # Should resolve Interface to Implementation
        instance1 = container.resolve(Interface)
        instance2 = container.resolve(Interface)

        self.assertIsInstance(instance1, Implementation)
        # Should be cached (same instance)
        self.assertIs(instance1, instance2)

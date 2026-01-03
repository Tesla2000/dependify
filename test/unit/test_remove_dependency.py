from unittest import TestCase

from dependify import DependencyInjectionContainer
from dependify import wired


class TestRemoveDependency(TestCase):

    def test_remove_dependency_basic(self):
        """
        Test if a dependency can be removed from the container.
        """
        container = DependencyInjectionContainer()

        class A:
            pass

        # Register dependency
        container.register(A)
        self.assertTrue(A in container)

        # Remove dependency
        container.remove(A)
        self.assertFalse(A in container)

    def test_remove_dependency_raises_if_not_present(self):
        """
        Test if removing a non-existent dependency raises an error.
        """
        container = DependencyInjectionContainer()

        class A:
            pass

        with self.assertRaises(ValueError):
            container.remove(A)

    def test_remove_dependency_with_multiple_registrations(self):
        """
        Test removing a specific dependency when multiple implementations are registered.
        """
        container = DependencyInjectionContainer()

        class Interface:
            pass

        class ImplementationA(Interface):
            pass

        class ImplementationB(Interface):
            pass

        # Register multiple implementations
        container.register(Interface, ImplementationA)
        container.register(Interface, ImplementationB)

        # Remove specific implementation
        container.remove(Interface, ImplementationB)

        # Should still have ImplementationA
        resolved = container.resolve(Interface)
        self.assertIsInstance(resolved, ImplementationA)

    def test_remove_all_dependencies_for_type(self):
        """
        Test removing all dependencies registered for a specific type.
        """
        container = DependencyInjectionContainer()

        class Interface:
            pass

        class ImplementationA(Interface):
            pass

        class ImplementationB(Interface):
            pass

        # Register multiple implementations
        container.register(Interface, ImplementationA)
        container.register(Interface, ImplementationB)
        self.assertTrue(Interface in container)

        # Remove all implementations
        container.remove(Interface)
        self.assertFalse(Interface in container)

    def test_remove_dependency_in_context_manager(self):
        """
        Test that dependency removal inside a context manager doesn't affect outer scope.
        """
        container = DependencyInjectionContainer()

        class A:
            pass

        # Register dependency in base container
        container.register(A)
        self.assertTrue(A in container)

        # Enter context and remove dependency
        with container:
            self.assertTrue(A in container)
            container.remove(A)
            self.assertFalse(A in container)

        # After exiting context, dependency should be back
        self.assertTrue(A in container)

    def test_add_and_remove_in_context_manager(self):
        """
        Test adding a dependency in context and removing it, then verify it's gone after context.
        """
        container = DependencyInjectionContainer()

        class A:
            pass

        class B:
            pass

        # Register A in base container
        container.register(A)

        with container:
            # Add B in context
            container.register(B)
            self.assertTrue(B in container)
            self.assertTrue(A in container)

            # Remove A in context
            container.remove(A)
            self.assertFalse(A in container)

        # After exiting: A should be back, B should be gone
        self.assertTrue(A in container)
        self.assertFalse(B in container)

    def test_remove_dependency_with_cached_instance(self):
        """
        Test that removing a cached dependency clears the cached instance.
        """
        container = DependencyInjectionContainer()

        class A:
            pass

        # Register with caching
        container.register(A, cached=True)

        # Resolve to create cached instance
        instance1 = container.resolve(A)

        # Remove dependency
        container.remove(A)

        # Re-register and resolve
        container.register(A, cached=True)
        instance2 = container.resolve(A)

        # Should be different instances
        self.assertIsNot(instance1, instance2)

    def test_remove_specific_implementation_lifo(self):
        """
        Test removing specific implementation maintains LIFO order for remaining dependencies.
        """
        container = DependencyInjectionContainer()

        class Service:
            pass

        class ServiceV1(Service):
            def version(self):
                return 1

        class ServiceV2(Service):
            def version(self):
                return 2

        class ServiceV3(Service):
            def version(self):
                return 3

        # Register in order: V1, V2, V3
        container.register(Service, ServiceV1)
        container.register(Service, ServiceV2)
        container.register(Service, ServiceV3)

        # Remove V2 (middle one)
        container.remove(Service, ServiceV2)

        # Resolve all - should get V3, V1 (LIFO order, without V2)
        all_services = list(container.resolve_all(Service))
        self.assertEqual(len(all_services), 2)
        self.assertEqual(all_services[0].version(), 3)  # V3 (most recent)
        self.assertEqual(all_services[1].version(), 1)  # V1

    def test_remove_dependency_then_resolve_fails(self):
        """
        Test that resolving a removed dependency raises ValueError.
        """
        container = DependencyInjectionContainer()

        class A:
            pass

        container.register(A)
        container.remove(A)

        with self.assertRaises(ValueError):
            container.resolve(A)

    def test_remove_in_nested_context_managers(self):
        """
        Test dependency removal in nested context managers.
        """
        container = DependencyInjectionContainer()

        class A:
            pass

        class B:
            pass

        # Register A and B in base
        container.register(A)
        container.register(B)

        with container:
            # First context level
            self.assertTrue(A in container)
            self.assertTrue(B in container)

            container.remove(A)
            self.assertFalse(A in container)

            with container:
                # Second context level
                self.assertFalse(A in container)
                self.assertTrue(B in container)

                container.remove(B)
                self.assertFalse(B in container)

            # Back to first context level - B should be back
            self.assertFalse(A in container)
            self.assertTrue(B in container)

        # Back to base - both should be back
        self.assertTrue(A in container)
        self.assertTrue(B in container)

    def test_remove_with_wired_decorator(self):
        """
        Test that removing a dependency affects @wired classes.
        """
        container = DependencyInjectionContainer()

        @wired(container=container)
        class Logger:
            def log(self, msg):
                return f"Log: {msg}"

        @wired(container=container)
        class Service:
            logger: Logger

        # First service instance works
        service1 = Service()
        self.assertIsInstance(service1.logger, Logger)

        # Remove Logger
        container.remove(Logger)

        # New service instance should fail to inject Logger
        with self.assertRaises(TypeError):
            Service()

    def test_remove_non_callable_value_dependency(self):
        """
        Test removing a non-callable value dependency.
        """
        container = DependencyInjectionContainer()

        class ApiKey:
            pass

        # Register a non-callable value
        api_key = "secret_key_123"
        container.register(ApiKey, api_key)
        self.assertTrue(ApiKey in container)

        # Resolve to verify it works
        resolved = container.resolve(ApiKey)
        self.assertEqual(resolved, api_key)

        # Remove the value dependency
        container.remove(ApiKey, api_key)
        self.assertFalse(ApiKey in container)

        # Should fail to resolve
        with self.assertRaises(ValueError):
            container.resolve(ApiKey)

    def test_remove_multiple_value_dependencies(self):
        """
        Test removing specific value from multiple registered values.
        """
        container = DependencyInjectionContainer()

        class Config:
            pass

        # Register multiple non-callable values
        config1 = {"env": "dev"}
        config2 = {"env": "prod"}
        config3 = {"env": "test"}

        container.register(Config, config1)
        container.register(Config, config2)
        container.register(Config, config3)

        # Remove the middle one
        container.remove(Config, config2)

        # Should get config3 (most recent remaining)
        resolved = container.resolve(Config)
        self.assertEqual(resolved, config3)

        # Verify all remaining
        all_configs = list(container.resolve_all(Config))
        self.assertEqual(len(all_configs), 2)
        self.assertEqual(all_configs[0], config3)  # LIFO - most recent
        self.assertEqual(all_configs[1], config1)

    def test_remove_value_when_target_is_none(self):
        """
        Test that when target is None (the actual value None), it can be removed.
        """
        container = DependencyInjectionContainer()

        class OptionalValue:
            pass

        container.register(OptionalValue)
        container.register(OptionalValue, None)
        self.assertTrue(OptionalValue in container)

        resolved = container.resolve(OptionalValue)
        self.assertIsNone(resolved)

        container.remove(OptionalValue, None)
        self.assertTrue(OptionalValue in container)

        resolved = container.resolve(OptionalValue)
        self.assertIsInstance(resolved, OptionalValue)

    def test_remove_string_value_dependency(self):
        """
        Test removing a string value dependency.
        """
        container = DependencyInjectionContainer()

        class DatabaseUrl:
            pass

        db_url = "postgresql://localhost/mydb"
        container.register(DatabaseUrl, db_url)

        # Verify it's registered
        self.assertTrue(DatabaseUrl in container)
        self.assertEqual(container.resolve(DatabaseUrl), db_url)

        # Remove it
        container.remove(DatabaseUrl, db_url)
        self.assertFalse(DatabaseUrl in container)

    def test_remove_integer_value_dependency(self):
        """
        Test removing an integer value dependency.
        """
        container = DependencyInjectionContainer()

        class Port:
            pass

        port = 8080
        container.register(Port, port)

        # Verify it's registered
        self.assertEqual(container.resolve(Port), port)

        # Remove it
        container.remove(Port, port)
        self.assertFalse(Port in container)

    def test_remove_dict_value_dependency(self):
        """
        Test removing a dict value dependency.
        """
        container = DependencyInjectionContainer()

        class Settings:
            pass

        settings = {"debug": True, "timeout": 30}
        container.register(Settings, settings)

        # Verify
        self.assertEqual(container.resolve(Settings), settings)

        # Remove
        container.remove(Settings, settings)
        self.assertFalse(Settings in container)

    def test_remove_list_value_dependency(self):
        """
        Test removing a list value dependency.
        """
        container = DependencyInjectionContainer()

        class AllowedHosts:
            pass

        hosts = ["localhost", "example.com", "api.example.com"]
        container.register(AllowedHosts, hosts)

        # Verify
        self.assertEqual(container.resolve(AllowedHosts), hosts)

        # Remove
        container.remove(AllowedHosts, hosts)
        self.assertFalse(AllowedHosts in container)

    def test_remove_object_instance_dependency(self):
        """
        Test removing a pre-instantiated object dependency.
        """
        container = DependencyInjectionContainer()

        class Config:
            def __init__(self, env: str):
                self.env = env

        # Create and register instance
        prod_config = Config(env="production")
        container.register(Config, prod_config)

        # Verify
        resolved = container.resolve(Config)
        self.assertIs(resolved, prod_config)

        # Remove
        container.remove(Config, prod_config)
        self.assertFalse(Config in container)

    def test_remove_value_in_context_manager(self):
        """
        Test removing value dependency in context manager doesn't affect outer scope.
        """
        container = DependencyInjectionContainer()

        class ApiKey:
            pass

        api_key = "secret_123"
        container.register(ApiKey, api_key)

        with container:
            # Verify it's available in context
            self.assertEqual(container.resolve(ApiKey), api_key)

            # Remove in context
            container.remove(ApiKey, api_key)
            self.assertFalse(ApiKey in container)

        # Should be back after context
        self.assertTrue(ApiKey in container)
        self.assertEqual(container.resolve(ApiKey), api_key)

"""
Tests to verify that decorator parameters can be overridden successfully.
Tests that __call__ parameters override __init__ parameters.
"""

from unittest import TestCase

from dependify import DependencyInjectionContainer
from dependify import Inject
from dependify import Injectable
from dependify import Injected
from dependify import Wired
from dependify.decorators import EvaluationStrategy


class TestDecoratorParameterOverride(TestCase):
    """Test suite for decorator parameter override functionality."""

    def setUp(self):
        self.container = DependencyInjectionContainer()

    def test_injectable_override_cached(self):
        """Test Injectable can override cached parameter"""
        # Create with cached=False
        injectable = Injectable(self.container, cached=False)

        @injectable
        class Service1:
            pass

        # Override with cached=True
        @injectable(cached=True)
        class Service2:
            pass

        # Service1 should not be cached
        instance1a = self.container.resolve(Service1)
        instance1b = self.container.resolve(Service1)
        self.assertIsNot(instance1a, instance1b)

        # Service2 should be cached
        instance2a = self.container.resolve(Service2)
        instance2b = self.container.resolve(Service2)
        self.assertIs(instance2a, instance2b)

    def test_injectable_override_autowire(self):
        """Test Injectable can override autowire parameter"""
        # Create with autowire=True (default)
        injectable = Injectable(self.container, autowire=True)

        class Dependency:
            pass

        self.container.register(Dependency)

        @injectable
        class Service1:
            def __init__(self, dep: Dependency):
                self.dep = dep

        # Should autowire
        instance1 = self.container.resolve(Service1)
        self.assertIsInstance(instance1.dep, Dependency)

        # Override with autowire=False
        @injectable(autowire=False)
        class Service2:
            def __init__(self, dep: Dependency):
                self.dep = dep

        # Should NOT autowire, so should fail
        with self.assertRaises(TypeError):
            self.container.resolve(Service2)

    def test_injectable_override_patch(self):
        """Test Injectable can override patch parameter"""
        # Create with no patch
        injectable = Injectable(self.container)

        class Base:
            def get_name(self):
                return "base"

        self.container.register(Base)

        @injectable
        class Implementation1(Base):
            def get_name(self):
                return "impl1"

        # Implementation1 registers itself, not as patch
        self.assertIsInstance(
            self.container.resolve(Implementation1), Implementation1
        )
        self.assertIsInstance(self.container.resolve(Base), Base)

        # Override with patch=Base
        @injectable(patch=Base)
        class Implementation2(Base):
            def get_name(self):
                return "impl2"

        # Implementation2 should replace Base
        resolved = self.container.resolve(Base)
        self.assertIsInstance(resolved, Implementation2)
        self.assertEqual(resolved.get_name(), "impl2")

    def test_injected_override_validate(self):
        """Test Injected can override validate parameter"""
        # Create with validate=True (will check types)
        injected = Injected(self.container, validate=True)

        @injected
        class Service1:
            name: str
            count: int

        # Should validate - this works
        service1 = Service1("test", 42)
        self.assertEqual(service1.name, "test")

        # Override with validate=False
        @injected(validate=False)
        class Service2:
            name: str
            count: int

        # Should not validate - wrong types should still work
        service2 = Service2("test", "not_an_int")
        self.assertEqual(service2.count, "not_an_int")

    def test_injected_override_evaluation_strategy(self):
        """Test Injected can override evaluation_strategy parameter"""
        # Create with EAGER strategy
        injected = Injected(
            self.container, evaluation_strategy=EvaluationStrategy.EAGER
        )

        class Database:
            def __init__(self):
                self.connected = True

        self.container.register(Database)

        @injected
        class Service1:
            db: Database
            name: str

        # With EAGER, db should be resolved immediately
        service1 = Service1(name="test1")
        self.assertIsInstance(service1.db, Database)

        # Override with LAZY strategy
        @injected(evaluation_strategy=EvaluationStrategy.LAZY)
        class Service2:
            db: Database
            name: str

        service2 = Service2(name="test2")
        # With LAZY, db should be a lazy resolver
        db = service2.db
        self.assertIsInstance(db, Database)

    def test_wired_override_cached(self):
        """Test Wired can override cached parameter"""
        # Create with cached=False
        wired = Wired(self.container, cached=False)

        @wired
        class Service1:
            def get_id(self):
                return id(self)

        # Override with cached=True
        @wired(cached=True)
        class Service2:
            def get_id(self):
                return id(self)

        # Service1 should not be cached
        instance1a = self.container.resolve(Service1)
        instance1b = self.container.resolve(Service1)
        self.assertIsNot(instance1a, instance1b)

        # Service2 should be cached
        instance2a = self.container.resolve(Service2)
        instance2b = self.container.resolve(Service2)
        self.assertIs(instance2a, instance2b)

    def test_wired_override_autowire(self):
        """Test Wired can override autowire parameter

        Note: With @wired, the Injected decorator creates __init__ which handles injection,
        so autowire parameter affects container.register behavior, not the __init__ creation.
        When autowire=False, the class is registered but without autowiring enabled,
        meaning it won't autowire dependencies when being resolved as a dependency itself.
        """
        # Create with autowire=True
        wired = Wired(self.container, autowire=True)

        @wired
        class Logger:
            pass

        @wired
        class Service1:
            logger: Logger
            name: str

        # Should work - Logger is available
        service1 = Service1(name="test")
        self.assertIsInstance(service1.logger, Logger)

        # Override with autowire=False - affects how Service2 is registered
        @wired(autowire=False)
        class Service2:
            logger: Logger
            name: str

        # Service2 still works when created directly because Injected creates the __init__
        # autowire=False affects container registration, not __init__ creation
        service2 = Service2(name="test2")
        self.assertIsInstance(service2.logger, Logger)

    def test_wired_override_validate(self):
        """Test Wired can override validate parameter"""
        # Create with validate=True
        wired = Wired(self.container, validate=True)

        @wired
        class Service1:
            name: str
            count: int

        # Should validate
        service1 = Service1("test", 42)
        self.assertEqual(service1.name, "test")

        # Override with validate=False
        @wired(validate=False)
        class Service2:
            name: str
            count: int

        # Should not validate
        service2 = Service2("test", "not_int")
        self.assertEqual(service2.count, "not_int")

    def test_wired_override_evaluation_strategy(self):
        """Test Wired can override evaluation_strategy parameter"""
        # Create with EAGER
        wired = Wired(
            self.container, evaluation_strategy=EvaluationStrategy.EAGER
        )

        @wired
        class Database:
            pass

        @wired
        class Service1:
            db: Database
            name: str

        # EAGER - db resolved immediately
        service1 = Service1(name="test1")
        self.assertIsInstance(service1.db, Database)

        # Override with LAZY
        @wired(evaluation_strategy=EvaluationStrategy.LAZY)
        class Service2:
            db: Database
            name: str

        service2 = Service2(name="test2")
        # LAZY - db resolved on access
        db = service2.db
        self.assertIsInstance(db, Database)

    def test_wired_override_patch(self):
        """Test Wired can override patch parameter"""
        wired = Wired(self.container)

        class Interface:
            def get_value(self):
                return "interface"

        self.container.register(Interface)

        @wired
        class Implementation1(Interface):
            def get_value(self):
                return "impl1"

        # No patch - Implementation1 registers itself
        self.assertIsInstance(
            self.container.resolve(Implementation1), Implementation1
        )

        # Override with patch
        @wired(patch=Interface)
        class Implementation2(Interface):
            def get_value(self):
                return "impl2"

        # Should patch Interface
        resolved = self.container.resolve(Interface)
        self.assertIsInstance(resolved, Implementation2)
        self.assertEqual(resolved.get_value(), "impl2")

    def test_multiple_overrides_same_decorator_instance(self):
        """Test that a single decorator instance can be used with different overrides"""
        injectable = Injectable(self.container, cached=False, autowire=True)

        # Use default (cached=False, autowire=True)
        @injectable
        class Service1:
            pass

        # Override both
        @injectable(cached=True, autowire=False)
        class Service2:
            pass

        # Override only cached
        @injectable(cached=True)
        class Service3:
            pass

        # Override only autowire
        @injectable(autowire=False)
        class Service4:
            pass

        # Verify Service1 (defaults)
        s1a = self.container.resolve(Service1)
        s1b = self.container.resolve(Service1)
        self.assertIsNot(s1a, s1b)

        # Verify Service2 (both overridden)
        s2a = self.container.resolve(Service2)
        s2b = self.container.resolve(Service2)
        self.assertIs(s2a, s2b)

        # Verify Service3 (cached overridden)
        s3a = self.container.resolve(Service3)
        s3b = self.container.resolve(Service3)
        self.assertIs(s3a, s3b)

    def test_inject_uses_container_from_init(self):
        """Test that Inject always uses the container from __init__"""
        container1 = DependencyInjectionContainer()
        container2 = DependencyInjectionContainer()

        class ApiKey:
            pass

        container1.register(ApiKey, "key1")
        container2.register(ApiKey, "key2")

        inject1 = Inject(container1)

        @inject1
        def func1(key: ApiKey):
            return key

        # Should use container1
        result1 = func1()
        self.assertEqual(result1, "key1")

        # Inject doesn't have override parameters since container is in __init__
        # This is the correct design - container should not change per call


if __name__ == "__main__":
    import unittest

    unittest.main()

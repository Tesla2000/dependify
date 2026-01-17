import inspect
from typing import ClassVar
from unittest import TestCase

from dependify import DependencyInjectionContainer
from dependify import injected
from dependify import wired
from dependify.decorators import EvaluationStrategy


class TestClassVar(TestCase):
    """Test suite to verify ClassVar fields are excluded from dependency injection."""

    def setUp(self):
        self.container = DependencyInjectionContainer()

    def test_class_var_in_init(self):
        """Test that ClassVar fields are not included in __init__ parameters"""

        @injected(container=self.container)
        class Service:
            counter: ClassVar[int] = 0
            name: str

        # Should be able to create without counter
        service = Service(name="TestService")
        self.assertEqual(service.name, "TestService")

        # ClassVar should be accessible as class attribute
        self.assertEqual(Service.counter, 0)

        # Modifying ClassVar should affect the class, not instance
        Service.counter = 5
        self.assertEqual(Service.counter, 5)

    def test_class_var_can_register_forbidden(self):
        """Test that ClassVar fields are not included in __init__ parameters"""
        with self.assertRaises(TypeError):
            self.container.register(ClassVar[int], 1)

    def test_class_var_with_registered_type_not_injected(self):
        """Test that ClassVar fields are not injected even if type is registered"""

        class Logger:
            def __init__(self):
                self.logs = []

        # Register Logger in container
        self.container.register(Logger)

        @injected(container=self.container)
        class Service:
            default_logger: ClassVar[Logger] = None  # Should NOT be injected
            name: str

        # Should work without providing default_logger
        service = Service(name="TestService")
        self.assertEqual(service.name, "TestService")

        # ClassVar should not be injected, remains as default
        self.assertIsNone(Service.default_logger)

    def test_class_var_with_registered_type_manual_assignment(self):
        """Test that ClassVar with registered type can be manually assigned"""

        class Logger:
            def __init__(self):
                self.level = "INFO"

        self.container.register(Logger)

        @injected(container=self.container)
        class Service:
            shared_logger: ClassVar[Logger]  # Not injected
            instance_logger: Logger  # Should be injected
            name: str

        # Manually assign the ClassVar
        Service.shared_logger = Logger()
        Service.shared_logger.level = "DEBUG"

        # Create instances - each gets its own injected logger
        service1 = Service(name="Service1")
        service2 = Service(name="Service2")

        # Instance loggers are separate
        self.assertIsInstance(service1.instance_logger, Logger)
        self.assertIsInstance(service2.instance_logger, Logger)
        self.assertIsNot(service1.instance_logger, service2.instance_logger)

        # ClassVar is shared
        self.assertEqual(Service.shared_logger.level, "DEBUG")
        self.assertIs(
            service1.__class__.shared_logger, service2.__class__.shared_logger
        )

    def test_class_var_vs_regular_field_same_type(self):
        """Test ClassVar and regular field of same type behave differently"""

        class Database:
            def __init__(self):
                self.connected = True

        self.container.register(Database)

        @injected(container=self.container)
        class Service:
            shared_db: ClassVar[Database]  # NOT injected
            instance_db: Database  # IS injected
            name: str

        # Set ClassVar manually
        Service.shared_db = Database()
        Service.shared_db.connected = False

        service = Service(name="TestService")

        # instance_db should be injected and separate from shared_db
        self.assertIsInstance(service.instance_db, Database)
        self.assertTrue(service.instance_db.connected)
        self.assertFalse(Service.shared_db.connected)
        self.assertIsNot(service.instance_db, Service.shared_db)

    def test_class_var_raises_type_error_if_provided(self):
        """Test that providing a ClassVar field in __init__ raises TypeError"""

        @injected(container=self.container)
        class Service:
            counter: ClassVar[int] = 0
            name: str

        Service(name="TestService", counter=10)

    def test_class_var_with_registered_type_raises_if_provided(self):
        """Test that providing a ClassVar[RegisteredType] in __init__ raises TypeError"""

        class Logger:
            def __init__(self):
                self.logs = []

        self.container.register(Logger)

        @injected(container=self.container)
        class Service:
            shared_logger: ClassVar[Logger]
            name: str

        logger = Logger()

        Service(name="TestService", shared_logger=logger)

    def test_multiple_class_vars_with_registered_types(self):
        """Test multiple ClassVar fields with registered types"""

        class Logger:
            def __init__(self):
                self.level = "INFO"

        class Database:
            def __init__(self):
                self.connected = True

        self.container.register(Logger)
        self.container.register(Database)

        @injected(container=self.container)
        class Service:
            default_logger: ClassVar[Logger]
            backup_db: ClassVar[Database]
            instance_count: ClassVar[int] = 0
            name: str
            active: bool

        service = Service(name="TestService", active=True)
        self.assertEqual(service.name, "TestService")
        self.assertEqual(service.active, True)

        # ClassVars should not be injected
        with self.assertRaises(AttributeError):
            _ = Service.default_logger

        with self.assertRaises(AttributeError):
            _ = Service.backup_db

        # Only the one with default should be accessible
        self.assertEqual(Service.instance_count, 0)

    def test_class_var_with_eager_strategy_and_registered_type(self):
        """Test ClassVar is not injected even with EAGER strategy"""

        class Logger:
            def __init__(self):
                self.logs = []

        self.container.register(Logger)

        @injected(
            container=self.container,
            evaluation_strategy=EvaluationStrategy.EAGER,
        )
        class Service:
            global_logger: ClassVar[Logger] = None  # Should NOT be injected
            instance_logger: Logger  # Should be injected eagerly
            name: str

        service = Service(name="TestService")

        # instance_logger should be injected
        self.assertIsInstance(service.instance_logger, Logger)
        self.assertEqual(service.name, "TestService")

        # global_logger should NOT be injected
        self.assertIsNone(Service.global_logger)

    def test_class_var_with_lazy_strategy_and_registered_type(self):
        """Test ClassVar is not injected even with LAZY strategy"""

        class Database:
            def __init__(self):
                self.connected = True

        self.container.register(Database)

        @injected(
            container=self.container,
            evaluation_strategy=EvaluationStrategy.LAZY,
        )
        class Service:
            connection_pool: ClassVar[Database] = (
                None  # Should NOT be injected
            )
            db: Database  # Should be injected lazily
            name: str

        service = Service(name="TestService")

        # db should be lazy-injected
        db = service.db
        self.assertIsInstance(db, Database)

        self.assertEqual(service.name, "TestService")

        # connection_pool should NOT be injected
        self.assertIsNone(Service.connection_pool)

    def test_class_var_with_optional_lazy_strategy_and_registered_type(self):
        """Test ClassVar is not injected even with OPTIONAL_LAZY strategy"""

        class Logger:
            def __init__(self):
                self.level = "INFO"

        @injected(
            container=self.container,
            evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY,
        )
        class Service:
            fallback_logger: ClassVar[Logger] = None  # Should NOT be injected
            logger: Logger  # Should be None (not registered)
            name: str

        service = Service(name="TestService")

        # logger should be None (not registered, but optional)
        self.assertIsNone(service.logger)

        self.assertEqual(service.name, "TestService")

        # fallback_logger should NOT be injected
        self.assertIsNone(Service.fallback_logger)

    def test_class_var_with_optional_lazy_strategy_and_unregistered_type(self):
        """Test ClassVar is not injected even with OPTIONAL_LAZY strategy"""

        @injected(
            container=self.container,
            evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY,
        )
        class Service:
            fallback_logger: ClassVar[int]

        service = Service()
        with self.assertRaises(AttributeError):
            _ = service.fallback_logger
        with self.assertRaises(AttributeError):
            _ = Service.fallback_logger

    def test_class_var_with_wired_and_registered_type(self):
        """Test ClassVar with @wired decorator and registered type"""

        class Logger:
            def __init__(self):
                self.level = "INFO"

        self.container.register(Logger)

        @wired(container=self.container)
        class Service:
            audit_logger: ClassVar[Logger]  # Should NOT be injected
            logger: Logger  # Should be injected
            name: str

        service = Service(name="TestService")

        # logger should be injected
        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.name, "TestService")

        # audit_logger should NOT be injected
        with self.assertRaises(AttributeError):
            _ = Service.audit_logger

    def test_class_var_with_inheritance_and_registered_types(self):
        """Test ClassVar with class inheritance and registered types"""

        class Logger:
            def __init__(self):
                self.level = "INFO"

        self.container.register(Logger)

        @injected(container=self.container)
        class BaseService:
            base_logger: ClassVar[Logger]
            name: str

        @injected(container=self.container)
        class ExtendedService(BaseService):
            extended_logger: ClassVar[Logger]
            instance_logger: Logger  # Should be injected
            version: str

        service = ExtendedService(name="Test", version="1.0")
        self.assertEqual(service.name, "Test")
        self.assertEqual(service.version, "1.0")

        # instance_logger should be injected
        self.assertIsInstance(service.instance_logger, Logger)

        # ClassVars should NOT be injected
        with self.assertRaises(AttributeError):
            _ = ExtendedService.base_logger

        with self.assertRaises(AttributeError):
            _ = ExtendedService.extended_logger

    def test_class_var_signature_check_with_registered_type(self):
        """Test that __init__ signature doesn't include ClassVar fields even if registered"""

        class Database:
            def __init__(self):
                self.connected = True

        self.container.register(Database)

        @injected(container=self.container)
        class Service:
            shared_db: ClassVar[Database]  # Should NOT be in signature
            instance_db: Database  # Should be in signature (as injected)
            name: str
            port: int

        sig = inspect.signature(Service.__init__)
        param_names = [p for p in sig.parameters.keys() if p != "self"]

        self.assertIn("name", param_names)
        self.assertIn("port", param_names)
        self.assertIn("instance_db", param_names)
        self.assertIn("shared_db", param_names)

    def test_class_var_annotations_preserved_with_registered_types(self):
        """Test that class annotations still include ClassVar fields"""

        class Logger:
            def __init__(self):
                self.logs = []

        self.container.register(Logger)

        @injected(container=self.container)
        class Service:
            shared_logger: ClassVar[Logger]
            instance_logger: Logger
            name: str

        # Annotations should include all fields
        self.assertIn("shared_logger", Service.__annotations__)
        self.assertIn("instance_logger", Service.__annotations__)
        self.assertIn("name", Service.__annotations__)

    def test_class_var_with_default_instance_and_registered_type(self):
        """Test ClassVar with a default instance of a registered type"""

        class Logger:
            def __init__(self, level="INFO"):
                self.level = level

        self.container.register(Logger)

        @injected(container=self.container)
        class Service:
            # ClassVar with default instance - should NOT trigger injection
            null_logger: ClassVar[Logger] = Logger(level="NULL")
            # Regular field - should be injected
            logger: Logger
            name: str

        service1 = Service(name="Service1")
        service2 = Service(name="Service2")

        # Each instance gets its own injected logger
        self.assertIsInstance(service1.logger, Logger)
        self.assertIsInstance(service2.logger, Logger)
        self.assertIsNot(service1.logger, service2.logger)

        # ClassVar is shared and has the default value
        self.assertEqual(Service.null_logger.level, "NULL")
        self.assertIs(
            service1.__class__.null_logger, service2.__class__.null_logger
        )

    def test_class_var_complex_scenario(self):
        """Test complex scenario with multiple registered types and ClassVars"""

        class Database:
            def __init__(self):
                self.connected = True

        class Cache:
            def __init__(self):
                self.data = {}

        class Logger:
            def __init__(self):
                self.level = "INFO"

        self.container.register(Database)
        self.container.register(Cache)
        self.container.register(Logger)

        @injected(container=self.container)
        class Service:
            # Class-level shared resources
            global_cache: ClassVar[Cache]
            metrics_db: ClassVar[Database]
            instance_count: ClassVar[int] = 0

            # Instance-level injected dependencies
            logger: Logger
            db: Database

            # Regular fields
            name: str
            port: int = 8080

            def __post_init__(self):
                Service.instance_count += 1

        # Manually set ClassVars
        Service.global_cache = Cache()
        Service.metrics_db = Database()

        service1 = Service(name="Service1")
        service2 = Service(name="Service2", port=9090)

        # Regular fields work correctly
        self.assertEqual(service1.name, "Service1")
        self.assertEqual(service1.port, 8080)
        self.assertEqual(service2.name, "Service2")
        self.assertEqual(service2.port, 9090)

        # Injected dependencies are instance-specific
        self.assertIsInstance(service1.logger, Logger)
        self.assertIsInstance(service1.db, Database)
        self.assertIsNot(service1.logger, service2.logger)
        self.assertIsNot(service1.db, service2.db)

        # ClassVars are shared
        self.assertEqual(Service.instance_count, 2)
        self.assertIs(
            service1.__class__.global_cache, service2.__class__.global_cache
        )
        self.assertIs(
            service1.__class__.metrics_db, service2.__class__.metrics_db
        )

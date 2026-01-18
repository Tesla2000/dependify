import unittest
from random import random
from typing import Annotated
from typing import ClassVar

from dependify import ConditionalResult
from dependify import DependencyInjectionContainer
from dependify import wired
from dependify.decorators import EvaluationStrategy
from dependify.decorators import Excluded
from dependify.decorators import Lazy
from dependify.decorators import OptionalLazy
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic import ValidationError
from typing_extensions import Self


class TestPydanticWired(unittest.TestCase):
    """Test suite for pydantic BaseModel integration with @wired decorator."""

    def setUp(self):
        self.container = DependencyInjectionContainer()

    def test_basic_pydantic_model_with_injection(self):
        """Test basic pydantic model with dependency injection"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, message: str):
                return f"LOG: {message}"

        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            name: str

        service = Service(name="TestService")
        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.name, "TestService")
        self.assertEqual(service.logger.log("test"), "LOG: test")

    def test_pydantic_model_with_multiple_dependencies(self):
        """Test pydantic model with multiple injected dependencies"""

        @wired(container=self.container)
        class Database(BaseModel):
            def query(self):
                return "DB_RESULT"

        @wired(container=self.container)
        class Cache(BaseModel):
            def get(self):
                return "CACHED"

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class Service(BaseModel):
            db: Database
            cache: Cache
            logger: Logger
            name: str
            port: int = 8080

        service = Service(name="MyService")

        self.assertIsInstance(service.db, Database)
        self.assertIsInstance(service.cache, Cache)
        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.name, "MyService")
        self.assertEqual(service.port, 8080)
        self.assertEqual(service.db.query(), "DB_RESULT")

    def test_pydantic_model_with_classvar(self):
        """Test that ClassVar fields are not injected in pydantic models"""

        @wired(container=self.container)
        class Logger(BaseModel):
            level: str = "INFO"

        @wired(container=self.container)
        class Service(BaseModel):
            shared_logger: ClassVar[Logger] = None
            instance_logger: Logger
            name: str

        # Manually set ClassVar
        Service.shared_logger = Logger(level="DEBUG")

        service1 = Service(name="Service1")
        service2 = Service(name="Service2")

        # Each instance gets its own injected logger
        self.assertIsInstance(service1.instance_logger, Logger)
        self.assertIsInstance(service2.instance_logger, Logger)
        self.assertIsNot(service1.instance_logger, service2.instance_logger)

        # ClassVar is shared
        self.assertEqual(Service.shared_logger.level, "DEBUG")
        self.assertIs(
            service1.__class__.shared_logger, service2.__class__.shared_logger
        )

    def test_pydantic_model_with_excluded_fields(self):
        """Test that Excluded fields work with pydantic models"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            name: str
            _internal_state: Annotated[dict, Excluded] = {}

            def model_post_init(self, __context) -> None:
                self._internal_state = {"initialized": True}

        service = Service(name="TestService")

        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.name, "TestService")
        self.assertEqual(service._internal_state, {"initialized": True})

    def test_pydantic_model_with_field_validators(self):
        """Test pydantic models with field validators and dependency injection"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            name: str
            port: int

            @field_validator("port")
            @classmethod
            def validate_port(cls, v):
                if v < 1024 or v > 65535:
                    raise ValueError("Port must be between 1024 and 65535")
                return v

        # Valid port
        service = Service(name="TestService", port=8080)
        self.assertEqual(service.port, 8080)
        self.assertIsInstance(service.logger, Logger)

        # Invalid port should raise validation error
        with self.assertRaises(ValueError) as cm:
            Service(name="TestService", port=100)
        self.assertIn("Port must be between 1024 and 65535", str(cm.exception))

    def test_pydantic_model_with_pydantic_field(self):
        """Test pydantic models with Field() for validation and metadata"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            name: str = Field(min_length=3, max_length=50)
            port: int = Field(default=8080, ge=1024, le=65535)
            debug: bool = Field(default=False)

        # Valid service
        service = Service(name="MyService")
        self.assertEqual(service.name, "MyService")
        self.assertEqual(service.port, 8080)
        self.assertEqual(service.debug, False)
        self.assertIsInstance(service.logger, Logger)

        # Test validation - name too short
        with self.assertRaises(ValueError):
            Service(name="AB")

        # Test validation - port out of range
        with self.assertRaises(ValueError):
            Service(name="ValidName", port=100)

    def test_pydantic_model_with_lazy_evaluation(self):
        """Test pydantic models with lazy dependency evaluation"""

        @wired(container=self.container)
        class ExpensiveDatabase(BaseModel):
            connected: bool = True

        @wired(container=self.container)
        class QuickLogger(BaseModel):
            ready: bool = True

        @wired(container=self.container)
        class Service(BaseModel):
            logger: QuickLogger
            _db: Annotated[ExpensiveDatabase, Lazy]
            name: str

        service = Service(name="TestService")

        # Logger should be available immediately (eager by default in pydantic)
        self.assertIsInstance(service.logger, QuickLogger)
        self.assertEqual(service.name, "TestService")

        # Database should be lazy
        db = service._db
        self.assertIsInstance(db, ExpensiveDatabase)
        self.assertTrue(db.connected)

    def test_pydantic_model_with_optional_lazy(self):
        """Test pydantic models with optional lazy dependencies"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        # Don't register Analytics service
        class Analytics(BaseModel):
            def track(self, event):
                return f"TRACKED: {event}"

        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            analytics: Annotated[Analytics, OptionalLazy] = None
            name: str

        service = Service(name="TestService")

        # Logger should be injected
        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.name, "TestService")

        # Analytics should be None (not registered)
        self.assertIsNone(service.analytics)

    def test_pydantic_model_with_nested_dependencies(self):
        """Test pydantic models with nested dependency injection"""

        @wired(container=self.container)
        class Database(BaseModel):
            def query(self):
                return "DATA"

        @wired(container=self.container)
        class Repository(BaseModel):
            db: Database
            table_name: str

            def get_all(self):
                return f"{self.table_name}: {self.db.query()}"

        @wired(container=self.container)
        class Service(BaseModel):
            repo: Repository
            name: str

            def fetch_data(self):
                return f"{self.name} -> {self.repo.get_all()}"

        # Repository needs to be manually created with table_name
        self.container.register(
            Repository, lambda: Repository(table_name="users")
        )

        service = Service(name="UserService")

        self.assertIsInstance(service.repo, Repository)
        self.assertEqual(service.name, "UserService")
        self.assertEqual(service.fetch_data(), "UserService -> users: DATA")

    def test_pydantic_model_override_injected_field(self):
        """Test that explicitly provided values override injected dependencies"""

        @wired(container=self.container)
        class Logger(BaseModel):
            level: str = "INFO"

        self.container.register(Logger, lambda: Logger(level="DEBUG"))

        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            name: str

        # Use default injected logger
        service1 = Service(name="Service1")
        self.assertEqual(service1.logger.level, "DEBUG")

        # Override with custom logger
        custom_logger = Logger(level="ERROR")
        service2 = Service(name="Service2", logger=custom_logger)
        self.assertEqual(service2.logger.level, "ERROR")

    def test_pydantic_model_with_model_config(self):
        """Test pydantic models with custom model_config"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class Service(BaseModel):
            model_config = {"frozen": True}

            logger: Logger
            name: str
            port: int = 8080

        service = Service(name="TestService")

        self.assertEqual(service.name, "TestService")
        self.assertEqual(service.port, 8080)
        self.assertIsInstance(service.logger, Logger)

        # Should not be able to modify frozen model
        with self.assertRaises(ValueError):
            service.name = "NewName"

    def test_pydantic_model_with_extra_fields(self):
        """Test pydantic models with extra='allow' or extra='forbid'"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class FlexibleService(BaseModel):
            model_config = {"extra": "allow"}

            logger: Logger
            name: str

        @wired(container=self.container)
        class StrictService(BaseModel):
            model_config = {"extra": "forbid"}

            logger: Logger
            name: str

        # Flexible service allows extra fields
        flexible = FlexibleService(name="Flexible", extra_field="extra")
        self.assertEqual(flexible.name, "Flexible")
        self.assertEqual(flexible.extra_field, "extra")
        self.assertIsInstance(flexible.logger, Logger)

        # Strict service forbids extra fields
        with self.assertRaises(ValueError):
            StrictService(name="Strict", extra_field="extra")

    def test_pydantic_model_cached_dependency(self):
        """Test pydantic models with cached dependencies"""

        @wired(container=self.container, cached=True)
        class SingletonLogger(BaseModel):
            instance_id: int = Field(
                default_factory=lambda: id(SingletonLogger)
            )

        @wired(container=self.container)
        class Service1(BaseModel):
            logger: SingletonLogger
            name: str

        @wired(container=self.container)
        class Service2(BaseModel):
            logger: SingletonLogger
            name: str

        service1 = Service1(name="Service1")
        service2 = Service2(name="Service2")

        # Both should share the same cached logger instance
        self.assertIs(service1.logger, service2.logger)
        self.assertEqual(
            service1.logger.instance_id, service2.logger.instance_id
        )

    def test_pydantic_model_with_complex_types(self):
        """Test pydantic models with complex field types"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            name: str
            tags: list[str] = []
            config: dict[str, int] = {}
            port: int | None = None

        service = Service(
            name="TestService",
            tags=["api", "web"],
            config={"timeout": 30, "retries": 3},
            port=8080,
        )

        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.name, "TestService")
        self.assertEqual(service.tags, ["api", "web"])
        self.assertEqual(service.config, {"timeout": 30, "retries": 3})
        self.assertEqual(service.port, 8080)

    def test_pydantic_model_inheritance(self):
        """Test pydantic model inheritance with dependency injection"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class BaseService(BaseModel):
            logger: Logger
            name: str

        @wired(container=self.container)
        class ExtendedService(BaseService):
            version: str
            debug: bool = False

        service = ExtendedService(name="MyService", version="1.0.0")

        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.name, "MyService")
        self.assertEqual(service.version, "1.0.0")
        self.assertEqual(service.debug, False)
        self.assertEqual(service.logger.log("test"), "LOG: test")

    def test_pydantic_model_with_custom_init(self):
        """Test pydantic models with custom __init__ are handled correctly"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        # Pydantic doesn't use __init__ in the traditional way
        # Instead we use model_post_init
        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            name: str
            _initialized: bool = False

            def model_post_init(self, __context) -> None:
                self._initialized = True

        service = Service(name="TestService")

        self.assertTrue(service._initialized)
        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.name, "TestService")

    def test_pydantic_model_json_serialization(self):
        """Test that pydantic models with injected dependencies can serialize"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class Service(BaseModel):
            model_config = {"arbitrary_types_allowed": True}

            logger: Logger
            name: str
            port: int = 8080

        service = Service(name="TestService")

        # Can't serialize the logger directly, but can serialize other fields
        data = service.model_dump(exclude={"logger"})
        self.assertEqual(data, {"name": "TestService", "port": 8080})

        # Check that logger is still accessible
        self.assertIsInstance(service.logger, Logger)

    def test_pydantic_model_with_computed_fields(self):
        """Test pydantic models with computed_field and dependency injection"""
        from pydantic import computed_field

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            name: str
            port: int = 8080

            @computed_field
            @property
            def url(self) -> str:
                return f"http://{self.name}:{self.port}"

        service = Service(name="localhost")

        self.assertEqual(service.url, "http://localhost:8080")
        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.name, "localhost")

    def test_pydantic_model_multiple_instances_separate_dependencies(self):
        """Test that multiple instances get separate dependency instances (non-cached)"""

        @wired(container=self.container, cached=False)
        class Logger(BaseModel):
            logger_id: float = Field(default_factory=random)

        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            name: str

        service1 = Service(name="Service1")
        service2 = Service(name="Service2")

        # Each service should have a different logger instance
        self.assertIsNot(service1.logger, service2.logger)
        self.assertNotEqual(
            service1.logger.logger_id, service2.logger.logger_id
        )

    def test_pydantic_model_with_validation_error(self):
        """Test that pydantic validation errors work correctly with injected fields"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            name: str = Field(min_length=5)
            port: int = Field(ge=1024, le=65535)

        # Logger is injected, but validation should still catch invalid fields
        with self.assertRaises(ValueError) as cm:
            Service(name="ABC", port=8080)
        self.assertIn("at least 5 characters", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            Service(name="ValidName", port=100)
        self.assertIn("greater than or equal to 1024", str(cm.exception))

    def test_pydantic_model_with_eager_strategy(self):
        """Test pydantic models with EAGER evaluation strategy"""

        @wired(container=self.container)
        class Database(BaseModel):
            connected: bool = True

        @wired(container=self.container)
        class Logger(BaseModel):
            ready: bool = True

        @wired(
            container=self.container,
            evaluation_strategy=EvaluationStrategy.EAGER,
        )
        class Service(BaseModel):
            db: Database
            logger: Logger
            name: str

        service = Service(name="TestService")

        # All dependencies should be immediately available
        self.assertIsInstance(service.db, Database)
        self.assertIsInstance(service.logger, Logger)
        self.assertTrue(service.db.connected)
        self.assertTrue(service.logger.ready)

    def test_pydantic_model_default_values_with_injection(self):
        """Test pydantic models with default values and injected dependencies"""

        @wired(container=self.container)
        class Logger(BaseModel):
            def log(self, msg):
                return f"LOG: {msg}"

        @wired(container=self.container)
        class Service(BaseModel):
            logger: Logger
            name: str = "DefaultService"
            port: int = 8080
            debug: bool = False

        # Use all defaults
        service1 = Service()
        self.assertEqual(service1.name, "DefaultService")
        self.assertEqual(service1.port, 8080)
        self.assertEqual(service1.debug, False)
        self.assertIsInstance(service1.logger, Logger)

        # Override some defaults
        service2 = Service(name="CustomService", debug=True)
        self.assertEqual(service2.name, "CustomService")
        self.assertEqual(service2.port, 8080)
        self.assertEqual(service2.debug, True)
        self.assertIsInstance(service2.logger, Logger)

    def test_pydantic_model_with_conditional_result(self):
        """Test pydantic models with ConditionalResult for context-aware injection"""

        @wired(container=self.container)
        class Application(BaseModel):
            role: str

        @wired(container=self.container)
        class AdminService(BaseModel):
            app: Application

        @wired(container=self.container)
        class UserService(BaseModel):
            app: Application

        @wired(container=self.container)
        class GuestService(BaseModel):
            app: Application

        self.container.register(
            Application,
            lambda: ConditionalResult(
                Application(role="default"),
                (
                    (
                        lambda class_: issubclass(class_, AdminService),
                        Application(role="admin"),
                    ),
                    (
                        lambda class_: issubclass(class_, UserService),
                        Application(role="user"),
                    ),
                ),
            ),
        )

        admin_service = AdminService()
        self.assertEqual(admin_service.app.role, "admin")

        user_service = UserService()
        self.assertEqual(user_service.app.role, "user")

        guest_service = GuestService()
        self.assertEqual(guest_service.app.role, "default")

    def test_pydantic_validation_applied(self):
        @wired(container=self.container)
        class Application(BaseModel):
            role: str = "too_long"

        @wired(container=self.container)
        class GuestService(BaseModel):
            app: Application

            @model_validator(mode="after")
            def _validate_field(self) -> Self:
                if len(self.app.role) > 5:
                    raise ValueError("Role too long")
                return self

        with self.assertRaises(ValidationError):
            GuestService()


if __name__ == "__main__":
    unittest.main()

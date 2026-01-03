from unittest import TestCase

from dependify import Dependency
from dependify import DependencyInjectionContainer
from dependify import inject
from dependify import wired


class TestNonCallableDependency(TestCase):

    def test_dependency_resolve_non_callable_string(self):
        """
        Test if a non-callable dependency (string) is resolved as a value instead of being called.
        """
        value = "test_value"
        dependency = Dependency(target=value)
        result = dependency.resolve()
        self.assertEqual(result, value)

    def test_dependency_resolve_non_callable_int(self):
        """
        Test if a non-callable dependency (int) is resolved as a value instead of being called.
        """
        value = 42
        dependency = Dependency(target=value)
        result = dependency.resolve()
        self.assertEqual(result, value)

    def test_dependency_resolve_non_callable_object(self):
        """
        Test if a non-callable dependency (pre-instantiated object) is resolved as a value.
        """

        class A:
            def __init__(self, value: int):
                self.value = value

        instance = A(100)
        dependency = Dependency(target=instance)
        result = dependency.resolve()
        self.assertIs(result, instance)
        self.assertEqual(result.value, 100)

    def test_dependency_resolve_non_callable_cached(self):
        """
        Test if a non-callable cached dependency returns the same value on multiple resolves.
        """
        value = {"key": "value"}
        dependency = Dependency(target=value, cached=True)
        result1 = dependency.resolve()
        result2 = dependency.resolve()
        self.assertIs(result1, result2)
        self.assertEqual(result1, value)

    def test_dependency_resolve_non_callable_list(self):
        """
        Test if a non-callable dependency (list) is resolved as a value.
        """
        value = [1, 2, 3]
        dependency = Dependency(target=value)
        result = dependency.resolve()
        self.assertEqual(result, value)

    def test_container_resolve_non_callable_string(self):
        """
        Test if the container can resolve a non-callable string dependency.
        """
        container = DependencyInjectionContainer()
        value = "configuration_value"
        container.register(str, value)
        result = container.resolve(str)
        self.assertEqual(result, value)

    def test_container_resolve_non_callable_dict(self):
        """
        Test if the container can resolve a non-callable dict dependency.
        """
        container = DependencyInjectionContainer()
        config = {"host": "localhost", "port": 8080}
        container.register(dict, config)
        result = container.resolve(dict)
        self.assertEqual(result, config)

    def test_inject_non_callable_dependency_in_class(self):
        """
        Test if a non-callable dependency can be injected into a class.
        """
        container = DependencyInjectionContainer()
        api_key = "secret_api_key_123"
        container.register(str, api_key)

        class Service:
            @inject(container=container)
            def __init__(self, key: str):
                self.key = key

        service = Service()
        self.assertEqual(service.key, api_key)

    def test_wired_with_non_callable_dependency(self):
        """
        Test if @wired decorator works with non-callable dependencies.
        """
        container = DependencyInjectionContainer()
        database_url = "postgresql://localhost:5432/mydb"
        container.register(str, database_url)

        @wired(container=container)
        class DatabaseService:
            db_url: str

            def get_url(self):
                return self.db_url

        service = DatabaseService()
        self.assertEqual(service.get_url(), database_url)

    def test_multiple_non_callable_dependencies_in_class(self):
        """
        Test if multiple non-callable dependencies can be injected into a class.
        """
        container = DependencyInjectionContainer()

        # Register different non-callable values
        api_key = "api_key_value"
        port = 8080
        config = {"debug": True}

        # Use custom types to avoid conflicts
        class ApiKey:
            pass

        class Port:
            pass

        class Config:
            pass

        container.register(ApiKey, api_key)
        container.register(Port, port)
        container.register(Config, config)

        class Application:
            @inject(container=container)
            def __init__(self, key: ApiKey, server_port: Port, cfg: Config):
                self.key = key
                self.server_port = server_port
                self.cfg = cfg

        app = Application()
        self.assertEqual(app.key, api_key)
        self.assertEqual(app.server_port, port)
        self.assertEqual(app.cfg, config)

    def test_non_callable_dependency_with_callable_dependency(self):
        """
        Test if non-callable and callable dependencies can coexist in the same class.
        """
        container = DependencyInjectionContainer()

        class Logger:
            def log(self, msg):
                return f"Log: {msg}"

        api_key = "my_secret_key"

        class ApiKeyType:
            pass

        container.register(Logger)
        container.register(ApiKeyType, api_key)

        class Service:
            @inject(container=container)
            def __init__(self, logger: Logger, key: ApiKeyType):
                self.logger = logger
                self.key = key

        service = Service()
        self.assertIsInstance(service.logger, Logger)
        self.assertEqual(service.key, api_key)
        self.assertEqual(service.logger.log("test"), "Log: test")

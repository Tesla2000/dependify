# Dependify

A powerful and flexible dependency injection framework for Python that makes managing dependencies simple and intuitive.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [The @wired Decorator](#the-wired-decorator)
  - [Basic Usage](#basic-usage)
  - [Dependency Injection](#dependency-injection)
  - [Caching (Singleton Pattern)](#caching-singleton-pattern)
  - [Patching Dependencies](#patching-dependencies)
  - [Custom Registries](#custom-registries)
- [Value Dependencies (Non-Callable)](#value-dependencies-non-callable)
  - [Basic Value Injection](#basic-value-injection)
  - [Configuration and Constants](#configuration-and-constants)
  - [Mixing Callable and Non-Callable Dependencies](#mixing-callable-and-non-callable-dependencies)
- [Context Managers](#context-managers)
- [Resolving Multiple Implementations](#resolving-multiple-implementations)
  - [Basic resolve_all Usage](#basic-resolve_all-usage)
  - [Plugin Systems](#plugin-systems)
  - [Event Subscribers](#event-subscribers)
  - [LIFO Ordering](#lifo-ordering)
  - [Updating Dependency Settings](#updating-dependency-settings)
- [Lazy Evaluation](#lazy-evaluation)
  - [Class-level Lazy Evaluation](#class-level-lazy-evaluation)
  - [Field-level Lazy Evaluation](#field-level-lazy-evaluation)
  - [Optional Lazy Dependencies](#optional-lazy-dependencies)
  - [Performance Benefits](#performance-benefits)
  - [Excluding Fields from __init__](#excluding-fields-from-__init__)
  - [ClassVar Fields](#classvar-fields)
- [Generics](#generics)
  - [Basic Generic Usage](#basic-generic-usage)
  - [Multiple Type Parameters](#multiple-type-parameters)
  - [Multiple Generic Instances with Different Types](#multiple-generic-instances-with-different-types)
  - [Generic Inheritance](#generic-inheritance)
  - [Abstract Generic Classes](#abstract-generic-classes)
  - [Generics with Caching](#generics-with-caching)
  - [Complex Generic Hierarchies](#complex-generic-hierarchies)
  - [Best Practices for Generics](#best-practices-for-generics)
- [Advanced Examples](#advanced-examples)
  - [Complex Service Architecture](#complex-service-architecture)
  - [Testing with Mocks](#testing-with-mocks)
  - [Conditional Dependencies](#conditional-dependencies)
  - [Removing Dependencies](#removing-dependencies)
- [API Reference](#api-reference)

## Installation

```bash
pip install dependify
```

## Quick Start

```python
from dependify import wired

@wired
class EmailService:
    def send(self, message: str):
        return f"Sending: {message}"

@wired
class NotificationService:
    email_service: EmailService
    
    def notify(self, user: str, message: str):
        return self.email_service.send(f"Hello {user}, {message}")

# Dependencies are automatically injected
service = NotificationService()
print(service.notify("Alice", "Welcome!"))
# Output: Sending: Hello Alice, Welcome!
```

## The @wired Decorator

The `@wired` decorator is the heart of Dependify. It combines the functionality of `@injectable` and `@injected`, automatically registering classes for dependency injection and generating constructors with dependency resolution.

### Basic Usage

The `@wired` decorator automatically handles dependency injection based on type annotations:

```python
from dependify import wired

@wired
class DatabaseConnection:
    def connect(self):
        return "Connected to database"

@wired
class UserRepository:
    db: DatabaseConnection  # Will be automatically injected
    
    def get_user(self, id: int):
        connection_status = self.db.connect()
        return f"User {id} fetched ({connection_status})"

# No need to manually inject dependencies
repo = UserRepository()
print(repo.get_user(123))
# Output: User 123 fetched (Connected to database)
```

### Dependency Injection

The `@wired` decorator automatically injects dependencies for annotated class attributes:

```python
@wired
class Logger:
    def log(self, message: str):
        print(f"[LOG] {message}")

@wired
class Cache:
    def get(self, key: str):
        return f"cached_{key}"

@wired
class ApiService:
    logger: Logger      # Automatically injected
    cache: Cache        # Automatically injected
    api_key: str        # Must be provided manually
    
    def fetch_data(self, endpoint: str):
        self.logger.log(f"Fetching from {endpoint}")
        cached = self.cache.get(endpoint)
        return f"Data from {endpoint}: {cached}"

# Only need to provide non-injectable parameters
service = ApiService(api_key="secret123")
print(service.fetch_data("/users"))
# Output: [LOG] Fetching from /users
#         Data from /users: cached_/users
```

### Multiple Dependencies

```python
@wired
class ServiceA:
    def get_a(self):
        return "A"

@wired
class ServiceB:
    def get_b(self):
        return "B"

@wired
class ServiceC:
    def get_c(self):
        return "C"

@wired
class Orchestrator:
    service_a: ServiceA
    service_b: ServiceB
    service_c: ServiceC
    
    def combine(self):
        return f"{self.service_a.get_a()}-{self.service_b.get_b()}-{self.service_c.get_c()}"

orchestrator = Orchestrator()
print(orchestrator.combine())  # Output: A-B-C
```

### Caching (Singleton Pattern)

Use `cached=True` to implement singleton behavior:

```python
@wired(cached=True)
class ConfigurationService:
    def __init__(self):
        self.id = id(self)  # Unique identifier for each instance
        self.settings = {"theme": "dark", "language": "en"}

@wired
class ComponentA:
    config: ConfigurationService

@wired
class ComponentB:
    config: ConfigurationService

# Both components share the same configuration instance
comp_a = ComponentA()
comp_b = ComponentB()

print(comp_a.config.id == comp_b.config.id)  # True - same instance
print(comp_a.config.settings == comp_b.config.settings)  # True

# Without caching, each injection creates a new instance
@wired(cached=False)
class NonCachedService:
    def __init__(self):
        self.id = id(self)

@wired
class ClientA:
    service: NonCachedService

@wired
class ClientB:
    service: NonCachedService

client_a = ClientA()
client_b = ClientB()
print(client_a.service.id == client_b.service.id)  # False - different instances
```

### Patching Dependencies

Use the `patch` parameter to replace existing dependencies (useful for testing):

```python
from dependify import wired, inject

class ProductionDatabase:
    def query(self, sql: str):
        return f"Production result for: {sql}"

@wired(patch=ProductionDatabase)
class TestDatabase:
    def query(self, sql: str):
        return f"Test mock result for: {sql}"

class DataService:
    @inject
    def __init__(self, db: ProductionDatabase):
        self.db = db
    
    def get_users(self):
        return self.db.query("SELECT * FROM users")

# The TestDatabase will be injected instead of ProductionDatabase
service = DataService()
print(service.get_users())
# Output: Test mock result for: SELECT * FROM users
```

### Custom Registries

Isolate dependencies using custom registries:

```python
from dependify import DependencyInjectionContainer, wired

# Create separate registries for different modules
auth_registry = DependencyInjectionContainer()
payment_registry = DependencyInjectionContainer()


# Authentication module
@wired(registry=auth_registry)
class TokenService:
    def generate_token(self):
        return "auth_token_xyz"


@wired(registry=auth_registry)
class AuthenticationService:
    token_service: TokenService

    def authenticate(self, username: str):
        token = self.token_service.generate_token()
        return f"User {username} authenticated with {token}"


# Payment module
@wired(registry=payment_registry)
class PaymentGateway:
    def process(self, amount: float):
        return f"Processing ${amount}"


@wired(registry=payment_registry)
class PaymentService:
    gateway: PaymentGateway

    def charge(self, user: str, amount: float):
        result = self.gateway.process(amount)
        return f"Charging {user}: {result}"


# Each registry maintains its own isolated dependencies
auth_service = AuthenticationService()
payment_service = PaymentService()

print(auth_service.authenticate("alice"))
# Output: User alice authenticated with auth_token_xyz

print(payment_service.charge("alice", 99.99))
# Output: Charging alice: Processing $99.99
```

## Value Dependencies (Non-Callable)

Dependify supports registering non-callable values (strings, numbers, objects, configurations) as dependencies. When a registered dependency is not callable, it is returned as-is instead of being invoked. This is useful for injecting configuration values, API keys, pre-instantiated objects, and other constants.

### Basic Value Injection

Register and inject simple values like strings, numbers, and objects:

```python
from dependify import DependencyInjectionContainer, inject

container = DependencyInjectionContainer()

# Register non-callable values
api_key = "secret_api_key_123"
port = 8080
config = {"debug": True, "timeout": 30}

# Register values with type hints
container.register(str, api_key)
container.register(int, port)
container.register(dict, config)

class Service:
    @inject(container=container)
    def __init__(self, key: str, server_port: int, cfg: dict):
        self.key = key
        self.server_port = server_port
        self.cfg = cfg

service = Service()
print(service.key)         # secret_api_key_123
print(service.server_port) # 8080
print(service.cfg)         # {'debug': True, 'timeout': 30}
```

### Configuration and Constants

Use custom types to avoid conflicts when registering multiple values of the same primitive type:

```python
from dependify import DependencyInjectionContainer, wired

container = DependencyInjectionContainer()

# Define custom types for different configuration values
class ApiKey:
    pass

class DatabaseUrl:
    pass

class CacheTimeout:
    pass

# Register configuration values
container.register(ApiKey, "my_api_key_xyz")
container.register(DatabaseUrl, "postgresql://localhost:5432/mydb")
container.register(CacheTimeout, 300)

@wired(container=container)
class Application:
    api_key: ApiKey
    db_url: DatabaseUrl
    cache_timeout: CacheTimeout

    def show_config(self):
        print(f"API Key: {self.api_key}")
        print(f"Database: {self.db_url}")
        print(f"Cache Timeout: {self.cache_timeout}s")

app = Application()
app.show_config()
# Output:
# API Key: my_api_key_xyz
# Database: postgresql://localhost:5432/mydb
# Cache Timeout: 300s
```

### Mixing Callable and Non-Callable Dependencies

Combine regular class dependencies with value dependencies in the same class:

```python
from dependify import DependencyInjectionContainer, wired

container = DependencyInjectionContainer()

@wired(container=container)
class Logger:
    def log(self, message: str):
        print(f"[LOG] {message}")

@wired(container=container)
class Database:
    def query(self, sql: str):
        return f"Results for: {sql}"

# Register a non-callable API key
class ApiKey:
    pass

container.register(ApiKey, "super_secret_key")

@wired(container=container)
class ApiService:
    logger: Logger          # Callable - creates new Logger instance
    db: Database            # Callable - creates new Database instance
    api_key: ApiKey         # Non-callable - injects the string value

    def fetch_data(self, endpoint: str):
        self.logger.log(f"Fetching from {endpoint} with key: {self.api_key}")
        return self.db.query(f"SELECT * FROM {endpoint}")

service = ApiService()
result = service.fetch_data("users")
# Output: [LOG] Fetching from users with key: super_secret_key
print(result)
# Output: Results for: SELECT * FROM users
```

### Pre-instantiated Objects

Register already-instantiated objects as dependencies:

```python
from dependify import DependencyInjectionContainer, wired

container = DependencyInjectionContainer()

class Config:
    def __init__(self, env: str, debug: bool):
        self.env = env
        self.debug = debug

# Create a pre-configured instance
production_config = Config(env="production", debug=False)

# Register the instance as a value
container.register(Config, production_config)

@wired(container=container)
class Application:
    config: Config

    def show_env(self):
        return f"Environment: {self.config.env}, Debug: {self.config.debug}"

app = Application()
print(app.show_env())
# Output: Environment: production, Debug: False

# All instances share the same config object
app2 = Application()
print(app.config is app2.config)  # True
```

### Best Practices for Value Dependencies

1. **Use custom types for clarity**: Define marker classes to distinguish between different string/int values
   ```python
   class ApiKey: pass
   class DatabaseUrl: pass
   # Better than registering multiple str types
   ```

2. **Pre-instantiate complex configurations**: Create configured objects once and inject them
   ```python
   config = ComplexConfig(many_params="...")
   container.register(ComplexConfig, config)
   ```

3. **Combine with caching**: Non-callable values are naturally singleton, but you can also cache callable dependencies
   ```python
   container.register(Logger, cached=True)  # Callable, cached
   container.register(ApiKey, "key_value")  # Non-callable, always same value
   ```

4. **Avoid primitive type conflicts**: Don't register multiple different values for `str`, `int`, etc. Use wrapper types instead

## Context Managers

Use context managers to temporarily modify dependency registrations:

```python
from dependify import DependencyInjectionContainer, injectable

registry = DependencyInjectionContainer()


@injectable(registry=registry)
class PermanentService:
    def get_name(self):
        return "permanent"


# Permanent registration
print(PermanentService in registry)  # True

# Temporary registration within context
with registry:
    @injectable(registry=registry)
    class TemporaryService:
        def get_name(self):
            return "temporary"


    print(TemporaryService in registry)  # True

    # Nested context for even more temporary registrations
    with registry:
        @injectable(registry=registry)
        class VeryTemporaryService:
            def get_name(self):
                return "very temporary"


        print(VeryTemporaryService in registry)  # True

    # VeryTemporaryService is gone after inner context
    print(VeryTemporaryService in registry)  # False
    print(TemporaryService in registry)  # Still True

# TemporaryService is gone after outer context
print(TemporaryService in registry)  # False
print(PermanentService in registry)  # Still True
```

### Practical Context Manager Example

```python
from dependify import DependencyInjectionContainer, wired

# Production configuration
prod_registry = DependencyInjectionContainer()


@wired(registry=prod_registry)
class EmailService:
    def send(self, to: str, message: str):
        # In production, actually send email
        return f"Email sent to {to}: {message}"


@wired(registry=prod_registry)
class NotificationSystem:
    email: EmailService

    def notify_user(self, user: str, message: str):
        return self.email.send(user, message)


# Testing with temporary mock
with prod_registry:
    @wired(registry=prod_registry, patch=EmailService)
    class MockEmailService:
        def send(self, to: str, message: str):
            return f"[MOCK] Email to {to}: {message}"


    # Within context, mock is used
    notifier = NotificationSystem()
    result = notifier.notify_user("test@example.com", "Test message")
    print(result)  # [MOCK] Email to test@example.com: Test message

# Outside context, production service is used
notifier = NotificationSystem()
result = notifier.notify_user("user@example.com", "Real message")
print(result)  # Email sent to user@example.com: Real message
```

## Resolving Multiple Implementations

Dependify allows you to register multiple implementations for the same type and resolve all of them at once using the `resolve_all` method. This is powerful for plugin systems, event subscribers, middleware pipelines, and chain-of-responsibility patterns.

### Basic resolve_all Usage

Register multiple implementations and resolve all of them:

```python
from dependify import DependencyInjectionContainer, wired

registry = DependencyInjectionContainer()

# Define an interface
class NotificationHandler:
    def send(self, message: str):
        raise NotImplementedError

@wired(registry=registry)
class EmailNotification(NotificationHandler):
    def send(self, message: str):
        return f"Email: {message}"

@wired(registry=registry)
class SmsNotification(NotificationHandler):
    def send(self, message: str):
        return f"SMS: {message}"

@wired(registry=registry)
class PushNotification(NotificationHandler):
    def send(self, message: str):
        return f"Push: {message}"

# Register all implementations
registry.register(NotificationHandler, EmailNotification)
registry.register(NotificationHandler, SmsNotification)
registry.register(NotificationHandler, PushNotification)

# Resolve all implementations - returns a generator
for handler in registry.resolve_all(NotificationHandler):
    print(handler.send("Hello!"))

# Output (in LIFO order - most recent first):
# Push: Hello!
# SMS: Hello!
# Email: Hello!

# Can also convert to list if needed
all_handlers = list(registry.resolve_all(NotificationHandler))
print(f"Total handlers: {len(all_handlers)}")  # Total handlers: 3
```

### Plugin Systems

Build flexible plugin architectures:

```python
from dependify import DependencyInjectionContainer, wired

registry = DependencyInjectionContainer()

class Plugin:
    """Base plugin interface"""
    def process(self, data: str) -> str:
        raise NotImplementedError

    def get_name(self) -> str:
        raise NotImplementedError

@wired(registry=registry)
class ValidationPlugin(Plugin):
    def process(self, data: str) -> str:
        return f"Validated: {data}"

    def get_name(self) -> str:
        return "Validator"

@wired(registry=registry)
class LoggingPlugin(Plugin):
    def process(self, data: str) -> str:
        return f"Logged: {data}"

    def get_name(self) -> str:
        return "Logger"

@wired(registry=registry)
class TransformPlugin(Plugin):
    def process(self, data: str) -> str:
        return f"Transformed: {data.upper()}"

    def get_name(self) -> str:
        return "Transformer"

# Register plugins
registry.register(Plugin, ValidationPlugin)
registry.register(Plugin, LoggingPlugin)
registry.register(Plugin, TransformPlugin)

class PluginManager:
    def __init__(self, registry: DependencyInjectionContainer):
        self.registry = registry

    def execute_pipeline(self, data: str):
        """Execute all plugins in sequence"""
        results = []
        for plugin in self.registry.resolve_all(Plugin):
            result = plugin.process(data)
            results.append(f"[{plugin.get_name()}] {result}")
        return results

manager = PluginManager(registry)
outputs = manager.execute_pipeline("user_input")
for output in outputs:
    print(output)

# Output (LIFO order):
# [Transformer] Transformed: USER_INPUT
# [Logger] Logged: user_input
# [Validator] Validated: user_input
```

### Event Subscribers

Implement event-driven architectures:

```python
from dependify import DependencyInjectionContainer, wired

registry = DependencyInjectionContainer()

class EventSubscriber:
    def on_user_registered(self, username: str, email: str):
        raise NotImplementedError

@wired(registry=registry)
class EmailSubscriber(EventSubscriber):
    def on_user_registered(self, username: str, email: str):
        print(f"📧 Sending welcome email to {email}")

@wired(registry=registry)
class AnalyticsSubscriber(EventSubscriber):
    def on_user_registered(self, username: str, email: str):
        print(f"📊 Tracking registration event for {username}")

@wired(registry=registry)
class SlackSubscriber(EventSubscriber):
    def on_user_registered(self, username: str, email: str):
        print(f"💬 Posting to Slack: New user {username}")

# Register all subscribers
registry.register(EventSubscriber, EmailSubscriber)
registry.register(EventSubscriber, AnalyticsSubscriber)
registry.register(EventSubscriber, SlackSubscriber)

class EventBus:
    def __init__(self, registry: DependencyInjectionContainer):
        self.registry = registry

    def publish_user_registered(self, username: str, email: str):
        """Notify all subscribers"""
        for subscriber in self.registry.resolve_all(EventSubscriber):
            subscriber.on_user_registered(username, email)

bus = EventBus(registry)
bus.publish_user_registered("alice", "alice@example.com")

# Output:
# 💬 Posting to Slack: New user alice
# 📊 Tracking registration event for alice
# 📧 Sending welcome email to alice@example.com
```

### LIFO Ordering

Dependencies are resolved in **LIFO (Last In First Out)** order - the most recently registered implementation appears first:

```python
from dependify import DependencyInjectionContainer

registry = DependencyInjectionContainer()

class Service:
    def get_priority(self) -> int:
        raise NotImplementedError

class LowPriority(Service):
    def get_priority(self) -> int:
        return 1

class MediumPriority(Service):
    def get_priority(self) -> int:
        return 2

class HighPriority(Service):
    def get_priority(self) -> int:
        return 3

# Register in order: Low -> Medium -> High
registry.register(Service, LowPriority)
registry.register(Service, MediumPriority)
registry.register(Service, HighPriority)

# Resolve all - LIFO order means High comes first
services = list(registry.resolve_all(Service))
priorities = [s.get_priority() for s in services]
print(priorities)  # [3, 2, 1] - High, Medium, Low

# Single resolve() returns the most recent (LIFO)
latest = registry.resolve(Service)
print(latest.get_priority())  # 3 - HighPriority

# Re-registering moves to the end (most recent)
registry.register(Service, LowPriority)  # Re-register LowPriority
services = list(registry.resolve_all(Service))
priorities = [s.get_priority() for s in services]
print(priorities)  # [1, 3, 2] - Low is now first (most recent)
```

### Updating Dependency Settings

Re-registering the same implementation with different settings updates the configuration:

```python
from dependify import DependencyInjectionContainer

registry = DependencyInjectionContainer()

class CacheService:
    def __init__(self):
        self.instance_id = id(self)

# Initial registration - not cached
registry.register(CacheService, CacheService, cached=False)

service1 = registry.resolve(CacheService)
service2 = registry.resolve(CacheService)
print(service1.instance_id == service2.instance_id)  # False - different instances

# Re-register with cached=True to update setting
registry.register(CacheService, CacheService, cached=True)

service3 = registry.resolve(CacheService)
service4 = registry.resolve(CacheService)
print(service3.instance_id == service4.instance_id)  # True - same instance (cached)
```

### Practical Example: Middleware Pipeline

Build a middleware processing pipeline:

```python
from dependify import DependencyInjectionContainer, wired

registry = DependencyInjectionContainer()

class Middleware:
    def process(self, request: dict) -> dict:
        raise NotImplementedError

@wired(registry=registry)
class AuthMiddleware(Middleware):
    def process(self, request: dict) -> dict:
        request['authenticated'] = True
        return request

@wired(registry=registry)
class LoggingMiddleware(Middleware):
    def process(self, request: dict) -> dict:
        request['logged'] = True
        print(f"Logging request: {request.get('path', '/')}")
        return request

@wired(registry=registry)
class RateLimitMiddleware(Middleware):
    def process(self, request: dict) -> dict:
        request['rate_limited'] = False
        return request

# Register middleware
registry.register(Middleware, AuthMiddleware)
registry.register(Middleware, LoggingMiddleware)
registry.register(Middleware, RateLimitMiddleware)

class RequestProcessor:
    def __init__(self, registry: DependencyInjectionContainer):
        self.registry = registry

    def handle_request(self, request: dict) -> dict:
        """Process request through middleware pipeline"""
        for middleware in self.registry.resolve_all(Middleware):
            request = middleware.process(request)
        return request

processor = RequestProcessor(registry)
request = {'path': '/api/users', 'method': 'GET'}
processed = processor.handle_request(request)

print(processed)
# Output: Logging request: /api/users
# {'path': '/api/users', 'method': 'GET', 'rate_limited': False,
#  'logged': True, 'authenticated': True}
```

## Lazy Evaluation

Dependify supports lazy evaluation of dependencies, allowing you to defer the creation of dependencies until they are actually needed. This can significantly improve performance, reduce startup time, and save resources for dependencies that may not be used in all code paths.

### Class-level Lazy Evaluation

Control when all dependencies of a class are instantiated using the `evaluation_strategy` parameter:

```python
from dependify import wired, EvaluationStrategy

@wired
class DatabaseConnection:
    def __init__(self):
        print("Database connected!")  # Expensive operation
        self.connected = True

@wired
class CacheService:
    def __init__(self):
        print("Cache initialized!")  # Another expensive operation
        self.ready = True

# EAGER evaluation (default) - dependencies created immediately
@wired(evaluation_strategy=EvaluationStrategy.EAGER)
class EagerService:
    db: DatabaseConnection
    cache: CacheService
    name: str

service = EagerService(name="MyService")
# Output immediately:
# Database connected!
# Cache initialized!

# LAZY evaluation - dependencies created on first access
@wired(evaluation_strategy=EvaluationStrategy.LAZY)
class LazyService:
    db: DatabaseConnection
    cache: CacheService
    name: str

service = LazyService(name="MyService")
# No output yet - dependencies not created

_ = service.db
# Output: Database connected!

_ = service.cache
# Output: Cache initialized!
```

### Field-level Lazy Evaluation

Mark specific fields for lazy evaluation using type markers with `Annotated`:

```python
from typing import Annotated
from dependify import wired, Lazy, OptionalLazy

@wired
class ExpensiveDatabase:
    def __init__(self):
        print("Connecting to expensive database...")
        # Simulate expensive connection
        self.connected = True

@wired
class QuickLogger:
    def __init__(self):
        print("Logger initialized quickly")
        self.ready = True

@wired
class OptionalCache:
    def __init__(self):
        print("Cache initialized")

# Mix eager and lazy fields in the same class
@wired  # Class defaults to EAGER
class MixedService:
    logger: QuickLogger                              # Eager (immediate)
    db: Annotated[ExpensiveDatabase, Lazy]          # Lazy (deferred)
    cache: Annotated[OptionalCache, OptionalLazy]   # Optional lazy
    name: str

service = MixedService(name="MyService")
# Output: Logger initialized quickly
# (Database and cache not created yet)

# Access lazy dependency when needed
connection = service.db
# Output: Connecting to expensive database...

# If OptionalCache is not registered, returns None instead of error
cache = service.cache  # Returns None or instance if registered
```

### Optional Lazy Dependencies

Use `OptionalLazy` for dependencies that might not be available:

```python
from typing import Annotated
from dependify import wired, OptionalLazy

@wired
class CoreService:
    """Always available"""
    def process(self):
        return "processed"

# AnalyticsService is NOT registered
class AnalyticsService:
    def track(self, event: str):
        return f"Tracked: {event}"

@wired
class Application:
    core: CoreService                                    # Required dependency
    analytics: Annotated[AnalyticsService, OptionalLazy]  # Optional dependency
    name: str

app = Application(name="MyApp")

# Core service works fine
print(app.core.process())  # Output: processed

# Analytics returns None since it's not registered (no error!)
if app.analytics:
    app.analytics.track("app_started")
else:
    print("Analytics not available")  # This branch executes
```

### Use OPTIONAL_LAZY for Class-level Optional Dependencies

```python
from dependify import injected, EvaluationStrategy

class FeatureFlag:
    """Optional feature - may not be registered"""
    def is_enabled(self, feature: str):
        return True

@injected(evaluation_strategy=EvaluationStrategy.OPTIONAL_LAZY)
class FeatureAwareService:
    feature_flags: FeatureFlag
    name: str

service = FeatureAwareService(name="MyService")

# Check if optional dependency is available
if service.feature_flags:
    enabled = service.feature_flags.is_enabled("new_feature")
else:
    enabled = False  # Default behavior when not available
```

### Performance Benefits

Lazy evaluation provides several advantages:

1. **Faster Startup**: Expensive dependencies only created when needed
```python
@wired(evaluation_strategy=EvaluationStrategy.LAZY)
class FastStartupService:
    expensive_ml_model: MachineLearningModel  # Only loaded if used
    heavy_database: DatabaseConnection        # Only connected if used
    large_cache: CacheService                 # Only initialized if used

    def quick_operation(self):
        # This can run without loading ML model
        return "fast"
```

2. **Conditional Usage**: Don't pay for dependencies you don't use
```python
@wired
class ConditionalService:
    db: Annotated[Database, Lazy]
    api: Annotated[ExternalAPI, Lazy]

    def get_data(self, use_cache: bool):
        if use_cache:
            return "cached_data"  # DB never created!
        return self.db.query()    # DB created only here
```

3. **Resource Efficiency**: Save memory and connections
```python
@wired
class ResourceEfficientService:
    # 10 different dependencies, but typically only 2-3 are used
    dep1: Annotated[Service1, Lazy]
    dep2: Annotated[Service2, Lazy]
    # ... more dependencies
    dep10: Annotated[Service10, Lazy]

    # Only creates what you actually use
```

4. **Graceful Degradation**: Optional dependencies enable fallback behavior
```python
@wired
class ResilientService:
    primary: PrimaryService
    analytics: Annotated[AnalyticsService, OptionalLazy]
    monitoring: Annotated[MonitoringService, OptionalLazy]

    def process(self, data):
        result = self.primary.process(data)

        # These are nice-to-have, not critical
        if self.analytics:
            self.analytics.track("processed", result)
        if self.monitoring:
            self.monitoring.record_metric("process_time", 42)

        return result
```

### Best Practices for Lazy Evaluation

1. **Use LAZY for expensive dependencies**: Database connections, ML models, large caches
2. **Use OptionalLazy for non-critical features**: Analytics, monitoring, experimental features
3. **Keep critical dependencies EAGER**: Configuration, logging, essential services
4. **Profile before optimizing**: Measure which dependencies benefit most from lazy loading
5. **Document lazy dependencies**: Make it clear which dependencies are lazy and why

### Excluding Fields from __init__

The `Excluded` marker allows you to define fields that should not be included as parameters in the generated `__init__` method. This is useful for internal state, computed properties, or fields that should be initialized after construction.

#### Basic Usage

```python
from typing import Annotated
from dependify import injected, Excluded

@injected
class Service:
    name: str                                  # Required in __init__
    port: int                                  # Required in __init__
    _cache: Annotated[dict, Excluded]         # NOT in __init__
    _metrics: Annotated[list, Excluded]       # NOT in __init__

# Only name and port are required
service = Service(name="MyService", port=8080)

# Excluded fields can be set manually after construction
service._cache = {}
service._metrics = []
```

#### Using __post_init__ to Initialize Excluded Fields

A common pattern is to initialize excluded fields in `__post_init__`:

```python
@injected
class Service:
    name: str
    _connection_pool: Annotated[dict, Excluded]
    _initialized: Annotated[bool, Excluded]

    def __post_init__(self):
        # Initialize excluded fields after construction
        self._connection_pool = {}
        self._initialized = True

service = Service(name="MyService")
print(service._initialized)  # True
```

#### Combining Excluded with Other Markers

Mix `Excluded` with `Lazy` and `OptionalLazy` for fine-grained control:

```python
from dependify import wired, Lazy, OptionalLazy, Excluded

@wired
class ComplexService:
    # Required parameter
    name: str

    # Eager dependency
    logger: Logger

    # Lazy dependency
    db: Annotated[Database, Lazy]

    # Optional lazy dependency
    cache: Annotated[Cache, OptionalLazy]

    # Excluded internal state
    _request_count: Annotated[int, Excluded]
    _last_request: Annotated[float, Excluded]

    def __post_init__(self):
        self._request_count = 0
        self._last_request = 0.0
```

#### When to Use Excluded

Use `Excluded` for:
1. **Internal state variables**: `_cache`, `_metrics`, `_state`
2. **Computed or derived fields**: Fields calculated from other fields
3. **Fields initialized in __post_init__**: State that depends on other fields
4. **Implementation details**: Internal bookkeeping not part of the public API
5. **Temporary or working data**: Data that shouldn't be part of construction

```python
@injected
class DataProcessor:
    source: DataSource
    config: Configuration

    # Internal state - not constructor parameters
    _buffer: Annotated[list, Excluded]
    _processed_count: Annotated[int, Excluded]
    _last_error: Annotated[Exception | None, Excluded]

    def __post_init__(self):
        self._buffer = []
        self._processed_count = 0
        self._last_error = None

    def process(self, data):
        self._buffer.append(data)
        self._processed_count += 1
        # Process data...
```

### ClassVar Fields

Python's `ClassVar` type hint indicates that a field is a class variable shared across all instances. Dependify respects `ClassVar` annotations and does not inject these fields, even if the type is registered in the container. ClassVar fields can be shadowed at the instance level by providing them as constructor parameters.

#### Basic ClassVar Usage

```python
from typing import ClassVar
from dependify import injected

@injected
class Service:
    instance_count: ClassVar[int] = 0  # Shared across all instances
    name: str                          # Instance-specific

    def __post_init__(self):
        Service.instance_count += 1

service1 = Service(name="Service1")
service2 = Service(name="Service2")

# ClassVar is shared
print(Service.instance_count)  # 2
print(service1.instance_count)  # 2 (accessed via class)
print(service2.instance_count)  # 2
```

#### ClassVar with Registered Types

ClassVar fields are never injected, even when their type is registered in the container:

```python
from typing import ClassVar
from dependify import wired

@wired
class Logger:
    def __init__(self):
        self.level = "INFO"

@wired
class Service:
    shared_logger: ClassVar[Logger] = None  # NOT injected
    instance_logger: Logger                 # IS injected
    name: str

# Manually set the ClassVar
Service.shared_logger = Logger()
Service.shared_logger.level = "DEBUG"

# Create instances - each gets its own injected logger
service1 = Service(name="Service1")
service2 = Service(name="Service2")

# Instance loggers are separate (injected)
print(service1.instance_logger is service2.instance_logger)  # False

# ClassVar is shared
print(service1.__class__.shared_logger is service2.__class__.shared_logger)  # True
print(Service.shared_logger.level)  # DEBUG
```

#### Shadowing ClassVar at Instance Level

ClassVar fields can be shadowed by providing them as constructor parameters, creating instance-specific values:

```python
from typing import ClassVar
from dependify import injected

@injected
class Service:
    default_timeout: ClassVar[int] = 30  # Class-level default
    name: str

# Use class default
service1 = Service(name="Service1")
print(service1.default_timeout)  # 30 (from class)

# Shadow with instance-specific value
service2 = Service(name="Service2", default_timeout=60)
print(service2.default_timeout)  # 60 (instance attribute)

# Class variable unchanged
print(Service.default_timeout)  # 30
print(service1.default_timeout)  # 30
```

#### ClassVar vs Regular Fields

The key difference is that ClassVar fields are not automatically injected:

```python
from typing import ClassVar
from dependify import wired

@wired
class Database:
    def __init__(self):
        self.connected = True

@wired
class Service:
    shared_db: ClassVar[Database]  # NOT injected (no default)
    instance_db: Database          # IS injected automatically
    name: str

# Must manually set ClassVar
Service.shared_db = Database()
Service.shared_db.connected = False

service = Service(name="MyService")

# instance_db is injected
print(service.instance_db.connected)  # True (new instance)

# shared_db is manually set
print(Service.shared_db.connected)  # False (shared instance)
print(service.instance_db is Service.shared_db)  # False
```

#### Complex Scenario with ClassVar

Combine ClassVar with injected dependencies and regular fields:

```python
from typing import ClassVar
from dependify import wired

@wired
class Database:
    def __init__(self):
        self.connected = True

@wired
class Cache:
    def __init__(self):
        self.data = {}

@wired
class Logger:
    def __init__(self):
        self.level = "INFO"

@wired
class Service:
    # Class-level shared resources (manually managed)
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

# Set up shared resources
Service.global_cache = Cache()
Service.metrics_db = Database()

# Create instances
service1 = Service(name="Service1")
service2 = Service(name="Service2", port=9090)

# Each instance has its own injected dependencies
print(service1.logger is service2.logger)  # False
print(service1.db is service2.db)  # False

# But shares ClassVar resources
print(service1.__class__.global_cache is service2.__class__.global_cache)  # True
print(Service.instance_count)  # 2
```

#### When to Use ClassVar

Use `ClassVar` for:

1. **Counters and statistics**: Track instance counts, request counts, etc.
   ```python
   instance_count: ClassVar[int] = 0
   total_requests: ClassVar[int] = 0
   ```

2. **Shared configuration**: Default values that apply to all instances
   ```python
   default_timeout: ClassVar[int] = 30
   max_retries: ClassVar[int] = 3
   ```

3. **Shared resources**: Connection pools, caches that should be shared
   ```python
   connection_pool: ClassVar[ConnectionPool]
   shared_cache: ClassVar[Cache]
   ```

4. **Constants and defaults**: Values that shouldn't be injected
   ```python
   VERSION: ClassVar[str] = "1.0.0"
   DEFAULT_BUFFER_SIZE: ClassVar[int] = 1024
   ```

5. **Type distinctions**: Clarify which fields are class-level vs instance-level
   ```python
   # Clear that these are shared, not per-instance
   _registry: ClassVar[dict] = {}
   _instances: ClassVar[list] = []
   ```

#### Best Practices for ClassVar

1. **Use defaults when possible**: Provide default values for ClassVar fields
   ```python
   counter: ClassVar[int] = 0  # Good
   # vs
   counter: ClassVar[int]  # Requires explicit assignment
   ```

2. **Initialize in module or class definition**: Set ClassVar values early
   ```python
   @wired
   class Service:
       pool: ClassVar[ConnectionPool] = ConnectionPool()
   ```

3. **Document shared state**: Make it clear when fields are shared
   ```python
   @wired
   class Service:
       # Shared across all instances - tracks total requests
       request_count: ClassVar[int] = 0
   ```

4. **Don't rely on injection for ClassVar**: Always set ClassVar manually
   ```python
   # Good
   Service.shared_logger = Logger()

   # Don't expect this to work (ClassVar is not injected)
   # Service.shared_logger will remain None unless manually set
   ```

## Generics

Dependify has full support for Python generics, allowing you to create type-safe, reusable components with dependency injection. You can use `Generic[T]` from the `typing` module with `@wired` classes to build flexible repositories, services, and other components.

### Basic Generic Usage

Create generic classes that work with different types:

```python
from typing import Generic, TypeVar
from dependify import wired

T = TypeVar("T")

@wired
class Repository(Generic[T]):
    """A generic repository that can store any type"""
    items: list[T]

    def __init__(self):
        self.items = []

    def add(self, item: T):
        self.items.append(item)
        return item

    def get_all(self) -> list[T]:
        return self.items

@wired
class User:
    name: str
    email: str

@wired
class UserService:
    repo: Repository[User]  # Type-specific repository

    def create_user(self, name: str, email: str):
        user = User(name=name, email=email)
        return self.repo.add(user)

# Register the specific generic type
from dependify import default_container
default_container.register(Repository[User], Repository)

service = UserService()
user = service.create_user("Alice", "alice@example.com")
print(f"Created: {user.name}")
# Output: Created: Alice
```

### Multiple Type Parameters

Use multiple type variables for more complex generic patterns:

```python
from typing import Generic, TypeVar
from dependify import wired

K = TypeVar("K")
V = TypeVar("V")

@wired
class KeyValueStore(Generic[K, V]):
    """A generic key-value store"""
    storage: dict[K, V]

    def __init__(self):
        self.storage = {}

    def set(self, key: K, value: V):
        self.storage[key] = value

    def get(self, key: K) -> V | None:
        return self.storage.get(key)

@wired
class User:
    name: str

@wired
class CacheService:
    user_cache: KeyValueStore[str, User]

    def cache_user(self, user_id: str, user: User):
        self.user_cache.set(user_id, user)

    def get_user(self, user_id: str) -> User | None:
        return self.user_cache.get(user_id)

# Register the specific generic type
from dependify import default_container
default_container.register(KeyValueStore[str, User], KeyValueStore)

cache = CacheService()
user = User(name="Bob")
cache.cache_user("user_123", user)
print(cache.get_user("user_123").name)
# Output: Bob
```

### Multiple Generic Instances with Different Types

Register and use the same generic class with different type arguments:

```python
from typing import Generic, TypeVar
from dependify import wired, DependencyInjectionContainer

T = TypeVar("T")

registry = DependencyInjectionContainer()

@wired(container=registry)
class Repository(Generic[T]):
    def __init__(self, entity_type: str):
        self.entity_type = entity_type
        self.items = []

    def get_type(self) -> str:
        return self.entity_type

class User:
    pass

class Product:
    pass

@wired(container=registry)
class Application:
    user_repo: Repository[User]
    product_repo: Repository[Product]

    def show_repositories(self):
        print(f"User repo type: {self.user_repo.get_type()}")
        print(f"Product repo type: {self.product_repo.get_type()}")

# Register different instances for each type
registry.register(Repository[User], lambda: Repository("User"))
registry.register(Repository[Product], lambda: Repository("Product"))

app = Application()
app.show_repositories()
# Output:
# User repo type: User
# Product repo type: Product
```

### Generic Inheritance

Build inheritance hierarchies with generics:

```python
from typing import Generic, TypeVar
from dependify import wired

T = TypeVar("T")

@wired
class BaseRepository(Generic[T]):
    """Base repository with common functionality"""
    base_initialized: bool = True

    def get_type_name(self) -> str:
        return "BaseRepository"

@wired
class User:
    name: str

@wired
class EnhancedUserRepository(BaseRepository[User]):
    """User-specific repository with enhanced features"""
    enhanced: bool = True

    def get_type_name(self) -> str:
        return "EnhancedUserRepository"

    def find_by_name(self, name: str):
        return f"Finding user: {name}"

@wired
class UserService:
    repo: EnhancedUserRepository

    def lookup_user(self, name: str):
        return self.repo.find_by_name(name)

service = UserService()
print(service.repo.get_type_name())  # EnhancedUserRepository
print(service.repo.base_initialized)  # True
print(service.lookup_user("Alice"))  # Finding user: Alice
```

### Abstract Generic Classes

Combine generics with abstract base classes for flexible architectures:

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional
from dependify import wired, DependencyInjectionContainer

T = TypeVar("T")
registry = DependencyInjectionContainer()

@wired(container=registry)
class Repository(ABC, Generic[T]):
    """Abstract repository interface"""

    @abstractmethod
    def save(self, item: T) -> bool:
        pass

    @abstractmethod
    def find(self, id: int) -> Optional[T]:
        pass

class User:
    def __init__(self, user_id: int, name: str):
        self.user_id = user_id
        self.name = name

@wired(container=registry)
class InMemoryUserRepository(Repository[User]):
    """Concrete implementation for User entities"""

    def __init__(self):
        self.storage = {}

    def save(self, item: User) -> bool:
        self.storage[item.user_id] = item
        return True

    def find(self, id: int) -> Optional[User]:
        return self.storage.get(id)

@wired(container=registry)
class UserService:
    repo: Repository[User]  # Depend on abstract type

    def create_and_find_user(self, user_id: int, name: str):
        user = User(user_id, name)
        self.repo.save(user)
        return self.repo.find(user_id)

# Register concrete implementation for abstract type
registry.register(Repository[User], InMemoryUserRepository)

service = UserService()
found_user = service.create_and_find_user(1, "Charlie")
print(f"Found: {found_user.name}")
# Output: Found: Charlie
```

### Generics with Caching

Use `cached=True` to share generic instances across your application:

```python
from typing import Generic, TypeVar
from dependify import wired, DependencyInjectionContainer

T = TypeVar("T")
registry = DependencyInjectionContainer()

@wired(container=registry, cached=True)
class SharedRepository(Generic[T]):
    """A shared singleton repository"""

    def __init__(self):
        self.instance_id = id(self)
        self.data = []

class User:
    pass

@wired(container=registry)
class ServiceA:
    repo: SharedRepository[User]

@wired(container=registry)
class ServiceB:
    repo: SharedRepository[User]

# Register as cached
registry.register(SharedRepository[User], SharedRepository, cached=True)

service_a = ServiceA()
service_b = ServiceB()

# Both services share the same repository instance
print(service_a.repo.instance_id == service_b.repo.instance_id)
# Output: True
```

### Complex Generic Hierarchies

Build sophisticated type hierarchies with nested generics:

```python
from typing import Generic, TypeVar
from dependify import wired, DependencyInjectionContainer

T = TypeVar("T")
U = TypeVar("U")

registry = DependencyInjectionContainer()

@wired(container=registry)
class BaseRepository(Generic[T]):
    """Base repository for any entity type"""
    level: str = "base"

@wired(container=registry)
class Service(Generic[T]):
    """Generic service that depends on a repository"""
    repo: BaseRepository[T]

class User:
    name: str = "DefaultUser"

@wired(container=registry)
class Application:
    """Application using specific service type"""
    user_service: Service[User]

    def get_repo_level(self):
        return self.user_service.repo.level

# Register the hierarchy
registry.register(BaseRepository[User], BaseRepository)
registry.register(
    Service[User],
    lambda: Service(registry.resolve(BaseRepository[User]))
)

app = Application()
print(f"Repository level: {app.get_repo_level()}")
# Output: Repository level: base
```

### Best Practices for Generics

1. **Register Specific Types**: Always register concrete generic types like `Repository[User]`, not the raw generic `Repository`
   ```python
   # Good
   registry.register(Repository[User], Repository)

   # Bad - won't work as expected
   registry.register(Repository, Repository)
   ```

2. **Use Abstract Base Classes**: Combine `ABC` with generics for flexible, testable designs
   ```python
   @wired
   class AbstractRepo(ABC, Generic[T]):
       @abstractmethod
       def save(self, item: T): pass
   ```

3. **Type Hints Everywhere**: Always annotate your generic type parameters for better IDE support
   ```python
   @wired
   class Service:
       repo: Repository[User]  # Clear and explicit
   ```

4. **Separate Instances for Different Types**: Each type specialization gets its own registration
   ```python
   registry.register(Repository[User], lambda: Repository("users"))
   registry.register(Repository[Product], lambda: Repository("products"))
   ```

5. **Use Caching Wisely**: Cache generic instances when they should be shared
   ```python
   # Shared configuration across all services
   registry.register(Config[AppSettings], Config, cached=True)
   ```

## Advanced Examples

### Complex Service Architecture

```python
from dependify import wired
from typing import List, Dict

@wired(cached=True)
class ConfigService:
    def __init__(self):
        self.config = {
            "db_host": "localhost",
            "db_port": 5432,
            "cache_ttl": 300
        }
    
    def get(self, key: str):
        return self.config.get(key)

@wired
class DatabaseService:
    config: ConfigService
    
    def connect(self):
        host = self.config.get("db_host")
        port = self.config.get("db_port")
        return f"Connected to {host}:{port}"

@wired(cached=True)
class CacheService:
    config: ConfigService
    
    def __init__(self):
        self.cache: Dict[str, any] = {}
    
    def get(self, key: str):
        return self.cache.get(key)
    
    def set(self, key: str, value: any):
        ttl = self.config.get("cache_ttl")
        self.cache[key] = value
        return f"Cached with TTL: {ttl}s"

@wired
class UserService:
    db: DatabaseService
    cache: CacheService
    
    def get_user(self, user_id: int):
        # Check cache first
        cached_user = self.cache.get(f"user_{user_id}")
        if cached_user:
            return f"From cache: {cached_user}"
        
        # Fetch from database
        self.db.connect()
        user = f"User#{user_id}"
        self.cache.set(f"user_{user_id}", user)
        return f"From database: {user}"

# Usage
service = UserService()
print(service.get_user(1))  # From database: User#1
print(service.get_user(1))  # From cache: User#1
```

### Testing with Mocks

```python
from dependify import DependencyInjectionContainer, wired


def create_test_environment():
    test_registry = DependencyInjectionContainer()

    @wired(registry=test_registry)
    class MockDatabase:
        def __init__(self):
            self.queries = []

        def execute(self, query: str):
            self.queries.append(query)
            return f"Mock result for: {query}"

    @wired(registry=test_registry)
    class MockCache:
        def __init__(self):
            self.data = {"test_key": "test_value"}

        def get(self, key: str):
            return self.data.get(key, "not_found")

    @wired(registry=test_registry)
    class ServiceUnderTest:
        db: MockDatabase
        cache: MockCache

        def process(self, key: str):
            cached = self.cache.get(key)
            if cached != "not_found":
                return f"Cached: {cached}"

            result = self.db.execute(f"SELECT * FROM table WHERE key='{key}'")
            return f"Database: {result}"

    return ServiceUnderTest, test_registry


# Run tests
ServiceClass, registry = create_test_environment()
service = ServiceClass()

# Test with cached data
print(service.process("test_key"))  # Cached: test_value

# Test with database query
print(service.process("new_key"))  # Database: Mock result for: SELECT * FROM table WHERE key='new_key'

# Verify mock was called
print(service.db.queries)  # ["SELECT * FROM table WHERE key='new_key'"]
```

### Conditional Dependencies

`ConditionalResult` enables context-aware dependency injection by providing different dependency instances based on the class receiving the injection. The conditional functions receive the **class** (not instance), allowing you to use `issubclass()` checks.

```python
from dependify import wired, ConditionalResult, DependencyInjectionContainer, injectable

registry = DependencyInjectionContainer()


@injectable(registry=registry)
class BaseLogger:
    def __init__(self, level: str):
        self.level = level

    def log(self, message: str):
        return f"[{self.level}] {message}"


@wired(registry=registry)
class ProductionService:
    logger: BaseLogger
    service_type: str = "production"


@wired(registry=registry)
class DevelopmentService:
    logger: BaseLogger
    service_type: str = "development"


@wired(registry=registry)
class TestService:
    logger: BaseLogger
    service_type: str = "test"


# Register conditional logger that provides different instances based on class
# Note: The lambda receives a CLASS, not an instance - use issubclass(), not isinstance()
registry.register(
    BaseLogger,
    lambda: ConditionalResult(
        BaseLogger("INFO"),  # Default
        (
            (lambda cls: issubclass(cls, ProductionService), BaseLogger("ERROR")),
            (lambda cls: issubclass(cls, DevelopmentService), BaseLogger("DEBUG")),
            (lambda cls: issubclass(cls, TestService), BaseLogger("TRACE")),
        )
    )
)

# Each service gets appropriate logger based on its class
prod = ProductionService()
dev = DevelopmentService()
test = TestService()

print(prod.logger.log("Production message"))  # [ERROR] Production message
print(dev.logger.log("Dev message"))  # [DEBUG] Dev message
print(test.logger.log("Test message"))  # [TRACE] Test message
```

**Key Points:**
- The condition callable receives a **class (type)**, not an instance
- Use `issubclass(cls, TargetClass)` to check class relationships
- Use `cls is TargetClass` for exact class matching
- Do NOT use `isinstance()` - it won't work as expected
- Conditions are evaluated in order; the first match wins
- If no condition matches, the default value is returned

### Removing Dependencies

Dependify allows you to remove dependencies from the container using the `remove()` method. This is useful for cleaning up temporary dependencies, testing scenarios, or dynamically managing your dependency graph.

#### Basic Removal

Remove all dependencies for a type or remove a specific implementation:

```python
from dependify import DependencyInjectionContainer

container = DependencyInjectionContainer()

class DatabaseService:
    def connect(self):
        return "Connected"

# Register the dependency
container.register(DatabaseService)
print(DatabaseService in container)  # True

# Remove all dependencies for this type
container.remove(DatabaseService)
print(DatabaseService in container)  # False

# Trying to resolve after removal will raise ValueError
try:
    container.resolve(DatabaseService)
except ValueError as e:
    print(f"Error: {e}")  # Error: name=<class 'DatabaseService'> couldn't be resolved
```

You can also use the `remove()` convenience function with the default container:

```python
from dependify import register, remove, has, wired

@wired
class EmailService:
    def send(self, msg):
        return f"Email: {msg}"

# EmailService is automatically registered by @wired
print(has(EmailService))  # True

# Remove it from the default container
remove(EmailService)
print(has(EmailService))  # False
```

#### Removing Specific Implementations

When multiple implementations are registered, you can remove a specific one:

```python
from dependify import DependencyInjectionContainer

container = DependencyInjectionContainer()

class NotificationService:
    pass

class EmailNotification(NotificationService):
    def send(self):
        return "Email sent"

class SMSNotification(NotificationService):
    def send(self):
        return "SMS sent"

class PushNotification(NotificationService):
    def send(self):
        return "Push notification sent"

# Register multiple implementations
container.register(NotificationService, EmailNotification)
container.register(NotificationService, SMSNotification)
container.register(NotificationService, PushNotification)

# Remove specific implementation
container.remove(NotificationService, SMSNotification)

# Remaining implementations are still available (LIFO order maintained)
all_notifications = list(container.resolve_all(NotificationService))
print(len(all_notifications))  # 2 (PushNotification and EmailNotification)
```

#### Removing Value Dependencies

Non-callable value dependencies can also be removed:

```python
from dependify import DependencyInjectionContainer

container = DependencyInjectionContainer()

class ApiKey:
    pass

class DatabaseUrl:
    pass

# Register value dependencies
api_key = "secret_key_123"
db_url = "postgresql://localhost/mydb"

container.register(ApiKey, api_key)
container.register(DatabaseUrl, db_url)

# Remove specific value
container.remove(ApiKey, api_key)
print(ApiKey in container)  # False

# DatabaseUrl is still available
print(container.resolve(DatabaseUrl))  # postgresql://localhost/mydb
```

#### Removing Dependencies with None Value

When you need to remove a dependency where the value is actually `None`, use the specific value:

```python
from dependify import DependencyInjectionContainer

container = DependencyInjectionContainer()

class OptionalConfig:
    pass

# Register both a class and None as separate dependencies
container.register(OptionalConfig)  # Registers the class itself
container.register(OptionalConfig, None)  # Registers None as a value

# Remove the None value specifically
container.remove(OptionalConfig, None)

# The class dependency is still there
result = container.resolve(OptionalConfig)
print(type(result).__name__)  # OptionalConfig
```

#### Removal in Context Managers

Dependencies removed inside a context manager are restored when exiting:

```python
from dependify import DependencyInjectionContainer, wired

container = DependencyInjectionContainer()

@wired(container=container)
class Logger:
    def log(self, msg):
        return f"Log: {msg}"

# Logger is registered
print(Logger in container)  # True

with container:
    # Remove Logger in context
    container.remove(Logger)
    print(Logger in container)  # False

    # Can't resolve inside context
    try:
        container.resolve(Logger)
    except ValueError:
        print("Logger not available in context")

# Logger is restored after exiting context
print(Logger in container)  # True
logger = container.resolve(Logger)
print(logger.log("Back!"))  # Log: Back!
```

#### Error Handling

Attempting to remove a non-existent dependency raises a `ValueError`:

```python
from dependify import DependencyInjectionContainer

container = DependencyInjectionContainer()

class NonExistent:
    pass

try:
    container.remove(NonExistent)
except ValueError as e:
    print(f"Error: {e}")  # Error: Dependency <class 'NonExistent'> is not registered
```

#### Use Cases for Removal

1. **Testing**: Remove production dependencies and replace with mocks
   ```python
   with container:
       container.remove(ProductionDatabase)
       container.register(ProductionDatabase, MockDatabase)
       # Run tests
   ```

2. **Dynamic Configuration**: Adjust dependencies based on runtime conditions
   ```python
   if not feature_enabled:
       container.remove(OptionalFeature)
   ```

3. **Cleanup**: Remove temporary dependencies after use
   ```python
   container.register(TempService, temp_instance)
   # Use temp_instance
   container.remove(TempService, temp_instance)
   ```

4. **Plugin Management**: Dynamically load/unload plugins
   ```python
   # Load plugin
   container.register(PluginInterface, MyPlugin)

   # Unload plugin
   container.remove(PluginInterface, MyPlugin)
   ```

### Working with Existing `__init__` Methods

The `@wired` decorator preserves existing `__init__` methods:

```python
@wired
class CustomInitService:
    def __init__(self):
        self.initialized = True
        self.counter = 0
        self.data = []
    
    def increment(self):
        self.counter += 1
        return self.counter

service = CustomInitService()
print(service.initialized)  # True
print(service.increment())  # 1
print(service.increment())  # 2
```

### Handling Circular Dependencies

Be aware that circular dependencies will raise an error:

```python
@wired
class ServiceA:
    b: "ServiceB"  # Forward reference

@wired
class ServiceB:
    a: ServiceA

# This will raise TypeError due to circular dependency
try:
    ServiceA()
except TypeError as e:
    print(f"Error: {e}")
    # Error: __init__() missing required positional arguments
```

## API Reference

### `@wired` Decorator

```python
def wired(
    class_: Optional[Type] = None,
    *,
    patch: Optional[Type] = None,
    cached: bool = False,
    autowire: bool = True,
    validate: bool = True,
    evaluation_strategy: EvaluationStrategy = EvaluationStrategy.EAGER,
    container: DependencyInjectionContainer = default_container
) -> Union[Type, Callable[[Type], Type]]
```

**Parameters:**
- `class_`: The class to decorate (automatically provided)
- `patch`: Replace this type in the registry
- `cached`: If True, creates singleton instances
- `autowire`: If True, automatically inject dependencies
- `validate`: If True, validate type annotations
- `evaluation_strategy`: When to create dependencies (`EAGER`, `LAZY`, or `OPTIONAL_LAZY`)
- `container`: The dependency container to use

### `@injected` Decorator

```python
def injected(
    class_: Optional[Type] = None,
    *,
    validate: bool = True,
    evaluation_strategy: EvaluationStrategy = EvaluationStrategy.EAGER,
    container: DependencyInjectionContainer = default_container
) -> Union[Type, Callable[[Type], Type]]
```

**Parameters:**
- `class_`: The class to decorate (automatically provided)
- `validate`: If True, validate type annotations
- `evaluation_strategy`: When to create dependencies (`EAGER`, `LAZY`, or `OPTIONAL_LAZY`)
- `container`: The dependency container to use

### `EvaluationStrategy` Enum

```python
class EvaluationStrategy(Enum):
    EAGER = "eager"           # Dependencies created immediately
    LAZY = "lazy"             # Dependencies created on first access
    OPTIONAL_LAZY = "optional_lazy"  # Returns None if not registered
```

### Field Markers

Use with `typing.Annotated` for field-level control:

```python
from typing import Annotated
from dependify import Lazy, OptionalLazy, Eager, Excluded

class MyService:
    # Force lazy evaluation for this field
    db: Annotated[Database, Lazy]

    # Optional lazy - returns None if not registered
    cache: Annotated[Cache, OptionalLazy]

    # Force eager evaluation (useful when class is lazy)
    logger: Annotated[Logger, Eager]

    # Exclude field from generated __init__
    _internal_state: Annotated[dict, Excluded]
```

**Available Markers:**
- `Lazy`: Defers dependency creation until first access
- `OptionalLazy`: Defers creation and returns `None` if dependency not registered
- `Eager`: Forces immediate creation (overrides class-level `LAZY`)
- `Excluded`: Excludes field from generated `__init__` method

### `DependencyInjectionContainer`

```python
class DependencyInjectionContainer:
    def register(self, name: Type, target: Optional[Union[Type, Callable]] = None,
                 cached: bool = False, autowired: bool = True) -> None
    def remove(self, name: Type, target: Any = NO_TARGET) -> None
    def resolve(self, name: Type) -> Any
    def resolve_all(self, name: Type) -> Generator[Any, None, None]
    def __contains__(self, name: Type) -> bool
    def clear(self) -> None
```

**Methods:**
- `register()`: Register a dependency (can register multiple for same type)
- `remove()`: Remove a dependency or all dependencies for a type
  - `name`: The type to remove dependencies for
  - `target`: The specific target to remove (defaults to `NO_TARGET` which removes all dependencies for the type)
  - Raises `ValueError` if the dependency is not registered
  - When used with a specific target, only that implementation is removed
  - Removal inside a context manager is isolated and reverted on exit
- `resolve()`: Resolve the most recently registered dependency (LIFO)
- `resolve_all()`: Resolve all registered dependencies for a type (returns generator in LIFO order)
- `__contains__()`: Check if a type has registered dependencies
- `clear()`: Clear all registrations

**Context Manager Support:**
```python
with registry:
    # Temporary registrations
    pass
# Registrations are reverted here
```

**NO_TARGET Constant:**

The `NO_TARGET` sentinel value is used to distinguish between removing all dependencies for a type vs. removing a dependency with value `None`:

```python
from dependify import DependencyInjectionContainer, NO_TARGET

container = DependencyInjectionContainer()

class Config:
    pass

# Register both a class and None
container.register(Config)
container.register(Config, None)

# Remove only the None value
container.remove(Config, None)  # Removes the dependency with target=None

# Remove all remaining dependencies
container.remove(Config)  # Same as container.remove(Config, NO_TARGET)
```

### Other Decorators

- `@injectable`: Register a class for dependency injection
- `@injected`: Auto-generate constructor with dependency injection
- `@inject`: Inject dependencies into a specific method

## Best Practices

1. **Use `@wired` for most cases** - It combines registration and injection
2. **Use custom containers** for module isolation and testing
3. **Use `cached=True`** for shared services and configuration
4. **Use context managers** for temporary overrides in tests
5. **Use lazy evaluation** for expensive or conditional dependencies
6. **Use `OptionalLazy`** for non-critical, optional features
7. **Use `Excluded`** for internal state that shouldn't be constructor parameters
8. **Avoid circular dependencies** by restructuring your architecture
9. **Type annotate all dependencies** for better IDE support and validation
10. **Use `remove()` with context managers for testing** - Remove and replace dependencies in isolated contexts to avoid affecting global state
11. **Prefer context managers over direct removal** - When testing, use context managers to ensure dependencies are restored automatically

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
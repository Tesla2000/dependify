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
- [Context Managers](#context-managers)
- [Advanced Examples](#advanced-examples)
  - [Complex Service Architecture](#complex-service-architecture)
  - [Testing with Mocks](#testing-with-mocks)
  - [Conditional Dependencies](#conditional-dependencies)
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
from dependify import DependencyRegistry, wired

# Create separate registries for different modules
auth_registry = DependencyRegistry()
payment_registry = DependencyRegistry()

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

## Context Managers

Use context managers to temporarily modify dependency registrations:

```python
from dependify import DependencyRegistry, injectable

registry = DependencyRegistry()

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
from dependify import DependencyRegistry, wired

# Production configuration
prod_registry = DependencyRegistry()

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
from dependify import DependencyRegistry, wired

def create_test_environment():
    test_registry = DependencyRegistry()
    
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
print(service.process("new_key"))   # Database: Mock result for: SELECT * FROM table WHERE key='new_key'

# Verify mock was called
print(service.db.queries)  # ["SELECT * FROM table WHERE key='new_key'"]
```

### Conditional Dependencies

```python
from dependify import wired, ConditionalResult, DependencyRegistry, injectable

registry = DependencyRegistry()

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

# Register conditional logger that provides different instances based on context
registry.register(
    BaseLogger,
    lambda: ConditionalResult(
        BaseLogger("INFO"),  # Default
        (
            (lambda instance: isinstance(instance, ProductionService), BaseLogger("ERROR")),
            (lambda instance: isinstance(instance, DevelopmentService), BaseLogger("DEBUG")),
            (lambda instance: isinstance(instance, TestService), BaseLogger("TRACE")),
        )
    )
)

# Each service gets appropriate logger
prod = ProductionService()
dev = DevelopmentService()
test = TestService()

print(prod.logger.log("Production message"))  # [ERROR] Production message
print(dev.logger.log("Dev message"))         # [DEBUG] Dev message
print(test.logger.log("Test message"))       # [TRACE] Test message
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
    registry: DependencyRegistry = default_registry
) -> Union[Type, Callable[[Type], Type]]
```

**Parameters:**
- `class_`: The class to decorate (automatically provided)
- `patch`: Replace this type in the registry
- `cached`: If True, creates singleton instances
- `autowire`: If True, automatically inject dependencies
- `validate`: If True, validate type annotations
- `registry`: The dependency registry to use

### `DependencyRegistry`

```python
class DependencyRegistry:
    def register(self, name: Type, target: Optional[Union[Type, Callable]] = None, 
                 cached: bool = False, autowired: bool = True) -> None
    def resolve(self, name: Type) -> Any
    def __contains__(self, name: Type) -> bool
    def clear(self) -> None
```

**Context Manager Support:**
```python
with registry:
    # Temporary registrations
    pass
# Registrations are reverted here
```

### Other Decorators

- `@injectable`: Register a class for dependency injection
- `@injected`: Auto-generate constructor with dependency injection
- `@inject`: Inject dependencies into a specific method

## Best Practices

1. **Use `@wired` for most cases** - It combines registration and injection
2. **Use custom registries** for module isolation and testing
3. **Use `cached=True`** for shared services and configuration
4. **Use context managers** for temporary overrides in tests
5. **Avoid circular dependencies** by restructuring your architecture
6. **Type annotate all dependencies** for better IDE support and validation

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
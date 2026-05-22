# Dependency Injection Container

## Overview

The AI Automation Framework includes a powerful Dependency Injection (DI) container that helps manage dependencies and improves code organization, testability, and maintainability.

## Features

- **Multiple Lifetimes**: Singleton, Transient, and Scoped
- **Constructor Injection**: Automatic dependency resolution via type hints
- **Factory Functions**: Complex initialization logic
- **Named Dependencies**: Multiple implementations of the same interface
- **Lazy Resolution**: Deferred dependency creation
- **Child Containers**: Scope isolation for request/session management
- **Circular Dependency Detection**: Prevents infinite loops
- **Thread-Safe**: Safe for concurrent use

## Installation

The DI container is part of the core framework:

```python
from ai_automation_framework.core.di import Container, Lifetime
```

## Basic Usage

### 1. Creating a Container

```python
from ai_automation_framework.core.di import Container

container = Container()
```

### 2. Registering Dependencies

#### Simple Registration

```python
# Register a concrete class
container.register(Logger, Logger, Lifetime.SINGLETON)

# Register interface with implementation
container.register(IEmailService, SMTPEmailService, Lifetime.SINGLETON)
```

#### Register Pre-created Instance

```python
logger = Logger()
container.register_instance(ILogger, logger)
```

#### Register with Factory Function

```python
def create_database(container: Container) -> Database:
    config = container.resolve(IConfig)
    return Database(config.get_connection_string())

container.register_factory(
    Database,
    create_database,
    Lifetime.SINGLETON
)
```

### 3. Resolving Dependencies

```python
# Resolve a dependency
logger = container.resolve(ILogger)

# Resolve named dependency
redis_cache = container.resolve(ICacheService, name="redis")
```

## Lifetimes

### Singleton

One instance for the entire application lifetime.

```python
container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)

logger1 = container.resolve(ILogger)
logger2 = container.resolve(ILogger)
# logger1 is logger2 -> True
```

**Use for**: Configuration, logging, caching, connection pools

### Transient

New instance every time it's resolved.

```python
container.register(IEmailService, EmailService, Lifetime.TRANSIENT)

service1 = container.resolve(IEmailService)
service2 = container.resolve(IEmailService)
# service1 is service2 -> False
```

**Use for**: Stateful operations, lightweight objects

### Scoped

One instance per scope (child container).

```python
container.register(IDatabase, Database, Lifetime.SCOPED)

with container.create_scope() as scope1:
    db1a = scope1.resolve(IDatabase)
    db1b = scope1.resolve(IDatabase)
    # db1a is db1b -> True

with container.create_scope() as scope2:
    db2 = scope2.resolve(IDatabase)
    # db1a is db2 -> False
```

**Use for**: Request-scoped data, unit of work patterns, database connections

## Constructor Injection

The container automatically resolves constructor parameters based on type hints:

```python
class UserService:
    def __init__(self, repository: IUserRepository, logger: ILogger):
        self.repository = repository
        self.logger = logger

# Register dependencies
container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
container.register(IUserRepository, UserRepository, Lifetime.SCOPED)
container.register(UserService, UserService, Lifetime.TRANSIENT)

# Resolve - dependencies are automatically injected
service = container.resolve(UserService)
```

### Optional Dependencies

```python
from typing import Optional

class Service:
    def __init__(self, logger: Optional[ILogger] = None):
        self.logger = logger or NullLogger()

# If ILogger is not registered, the parameter is skipped
```

## Named Dependencies

Register multiple implementations with names:

```python
# Register multiple cache implementations
container.register(ICacheService, RedisCache, Lifetime.SINGLETON, name="redis")
container.register(ICacheService, MemoryCache, Lifetime.SINGLETON, name="memory")

# Resolve by name
redis = container.resolve(ICacheService, name="redis")
memory = container.resolve(ICacheService, name="memory")
```

## Lazy Resolution

Defer dependency creation until first use:

```python
class WorkerService:
    def __init__(self, logger: ILogger):
        self.logger = logger
        # Create lazy proxy - ExpensiveService not created yet
        self.expensive = container.resolve_lazy(ExpensiveService)

    def do_work(self):
        # ExpensiveService is created on first access
        return self.expensive.process()
```

## Scoped Containers

Create child containers for scope isolation:

```python
# Root container with shared services
container = Container()
container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
container.register(IDatabase, Database, Lifetime.SCOPED)

# Process request 1
with container.create_scope() as scope1:
    db1 = scope1.resolve(IDatabase)
    # Use db1...

# Process request 2 with different scope
with container.create_scope() as scope2:
    db2 = scope2.resolve(IDatabase)
    # Use db2...
    # db1 != db2
```

## Error Handling

### Resolution Errors

```python
try:
    service = container.resolve(IUnregisteredService)
except ResolutionError as e:
    print(f"Service not found: {e}")
```

### Circular Dependencies

```python
class ServiceA:
    def __init__(self, service_b: ServiceB):
        pass

class ServiceB:
    def __init__(self, service_a: ServiceA):
        pass

container.register(ServiceA, ServiceA)
container.register(ServiceB, ServiceB)

try:
    container.resolve(ServiceA)
except CircularDependencyError as e:
    print(f"Circular dependency: {e}")
```

## Best Practices

### 1. Register Dependencies at Application Startup

```python
def configure_services(container: Container) -> None:
    # Infrastructure
    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
    container.register(IConfig, AppConfig, Lifetime.SINGLETON)

    # Data Access
    container.register(IDatabase, PostgresDatabase, Lifetime.SCOPED)
    container.register(IUserRepository, UserRepository, Lifetime.SCOPED)

    # Services
    container.register(IUserService, UserService, Lifetime.TRANSIENT)
```

### 2. Use Interfaces (Protocols)

```python
from typing import Protocol

class ILogger(Protocol):
    def log(self, message: str) -> None:
        ...

class ConsoleLogger:
    def log(self, message: str) -> None:
        print(message)

# Register against interface
container.register(ILogger, ConsoleLogger)
```

### 3. Keep Constructors Simple

```python
# Good - simple constructor with dependencies
class UserService:
    def __init__(self, repository: IUserRepository, logger: ILogger):
        self.repository = repository
        self.logger = logger

# Avoid - complex initialization in constructor
class BadService:
    def __init__(self, config: IConfig):
        self.connection = self._create_connection()  # Bad!
        self.data = self._load_data()  # Bad!
```

### 4. Use Factory Functions for Complex Setup

```python
def create_database_pool(container: Container) -> DatabasePool:
    config = container.resolve(IConfig)
    logger = container.resolve(ILogger)

    pool = DatabasePool(
        host=config.get("db_host"),
        port=int(config.get("db_port")),
        pool_size=int(config.get("pool_size")),
        logger=logger
    )

    # Complex initialization
    pool.initialize()
    pool.warm_up()

    return pool

container.register_factory(DatabasePool, create_database_pool, Lifetime.SINGLETON)
```

### 5. Use Scopes for Request Handling

```python
def handle_request(container: Container, request: Request) -> Response:
    with container.create_scope() as scope:
        # Register request-specific data
        scope.register_instance(Request, request)

        # Resolve handler with request-scoped dependencies
        handler = scope.resolve(RequestHandler)
        return handler.handle()
```

## Testing with DI Container

### Mock Dependencies for Testing

```python
import unittest
from unittest.mock import Mock

class TestUserService(unittest.TestCase):
    def test_create_user(self):
        # Create container for test
        container = Container()

        # Register mocks
        mock_repository = Mock(spec=IUserRepository)
        mock_logger = Mock(spec=ILogger)

        container.register_instance(IUserRepository, mock_repository)
        container.register_instance(ILogger, mock_logger)
        container.register(UserService, UserService)

        # Test
        service = container.resolve(UserService)
        service.create_user("test@example.com")

        # Verify
        mock_repository.create.assert_called_once()
```

### Test Isolation

```python
def setUp(self):
    self.container = Container()
    self.configure_test_dependencies()

def tearDown(self):
    self.container.clear()  # Clean up between tests
```

## Advanced Patterns

### 1. Child Containers for Multi-Tenancy

```python
# Root container with shared services
root = Container()
root.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)

# Tenant-specific containers
def create_tenant_scope(tenant_id: str) -> Container:
    tenant_scope = root.create_scope()

    # Register tenant-specific services
    tenant_scope.register_factory(
        IDatabase,
        lambda c: Database(f"tenant_{tenant_id}_db"),
        Lifetime.SCOPED
    )

    return tenant_scope

# Use for tenant 1
with create_tenant_scope("tenant1") as scope:
    service = scope.resolve(UserService)
```

### 2. Decorator Pattern with DI

```python
class LoggingDecorator:
    def __init__(self, inner: IUserService, logger: ILogger):
        self.inner = inner
        self.logger = logger

    def create_user(self, email: str) -> User:
        self.logger.log(f"Creating user: {email}")
        result = self.inner.create_user(email)
        self.logger.log(f"User created: {result.id}")
        return result

# Register with decorator
container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
container.register(UserService, UserService, Lifetime.TRANSIENT)

container.register_factory(
    IUserService,
    lambda c: LoggingDecorator(
        c.resolve(UserService),
        c.resolve(ILogger)
    ),
    Lifetime.TRANSIENT
)
```

### 3. Configuration-Based Registration

```python
def configure_from_config(container: Container, config: dict) -> None:
    # Register logger based on config
    if config.get("logger") == "console":
        container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
    elif config.get("logger") == "file":
        container.register(ILogger, FileLogger, Lifetime.SINGLETON)

    # Register database based on config
    db_type = config.get("database")
    if db_type == "postgres":
        container.register(IDatabase, PostgresDatabase, Lifetime.SCOPED)
    elif db_type == "mysql":
        container.register(IDatabase, MySQLDatabase, Lifetime.SCOPED)
```

## API Reference

### Container Class

#### Methods

- `register(service_type, implementation, lifetime, name)` - Register a service
- `register_instance(service_type, instance, name)` - Register a pre-created instance
- `register_factory(service_type, factory, lifetime, name)` - Register a factory function
- `resolve(service_type, name)` - Resolve a dependency
- `resolve_lazy(service_type, name)` - Create a lazy proxy
- `create_scope()` - Create a child container
- `is_registered(service_type, name)` - Check if service is registered
- `clear()` - Clear all registrations

### Lifetime Enum

- `Lifetime.SINGLETON` - One instance for entire container
- `Lifetime.TRANSIENT` - New instance every time
- `Lifetime.SCOPED` - One instance per scope

### Exceptions

- `DIError` - Base exception
- `ResolutionError` - Cannot resolve dependency
- `CircularDependencyError` - Circular dependency detected
- `RegistrationError` - Invalid registration

## Examples

See `/home/user/Automation_with_AI/examples/di_container_example.py` for comprehensive examples covering all features.

## Migration Guide

### From Manual Dependency Management

**Before:**
```python
class UserService:
    def __init__(self):
        self.config = Config()
        self.logger = Logger()
        self.repository = UserRepository(self.config, self.logger)
```

**After:**
```python
class UserService:
    def __init__(self, repository: IUserRepository, logger: ILogger):
        self.repository = repository
        self.logger = logger

# At application startup
container.register(ILogger, Logger, Lifetime.SINGLETON)
container.register(IConfig, Config, Lifetime.SINGLETON)
container.register(IUserRepository, UserRepository, Lifetime.SCOPED)
container.register(UserService, UserService, Lifetime.TRANSIENT)
```

## Troubleshooting

### "No registration found" Error

Make sure the service is registered before resolving:

```python
container.register(ILogger, ConsoleLogger)
logger = container.resolve(ILogger)  # Now works
```

### Circular Dependencies

Refactor to break the cycle:

```python
# Bad - circular dependency
class A:
    def __init__(self, b: B): ...

class B:
    def __init__(self, a: A): ...

# Good - extract shared dependency
class Shared:
    pass

class A:
    def __init__(self, shared: Shared): ...

class B:
    def __init__(self, shared: Shared): ...
```

### Forward References Not Working

Use string annotations at module level:

```python
from __future__ import annotations

class ServiceA:
    def __init__(self, service_b: ServiceB):  # Works
        pass

class ServiceB:
    pass
```

## Performance Considerations

- **Singleton creation**: Only created once, minimal overhead
- **Transient creation**: New instance each time, slightly more overhead
- **Scoped creation**: One per scope, balanced performance
- **Thread safety**: Uses RLock, safe for concurrent access
- **Resolution caching**: Singletons and scoped instances are cached

## Conclusion

The Dependency Injection container provides a robust foundation for building maintainable, testable applications. By inverting control and managing dependencies centrally, your code becomes more modular and easier to test.

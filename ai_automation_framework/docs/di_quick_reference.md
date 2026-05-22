# Dependency Injection - Quick Reference

## Import

```python
from ai_automation_framework.core import Container, Lifetime
```

## Basic Operations

### Create Container
```python
container = Container()
```

### Register Services

```python
# Simple registration
container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)

# Register instance
logger = ConsoleLogger()
container.register_instance(ILogger, logger)

# Register factory
container.register_factory(
    IDatabase,
    lambda c: Database(c.resolve(IConfig)),
    Lifetime.SCOPED
)

# Named registration
container.register(ICacheService, RedisCache, Lifetime.SINGLETON, name="redis")
```

### Resolve Services

```python
# Simple resolution
logger = container.resolve(ILogger)

# Named resolution
cache = container.resolve(ICacheService, name="redis")

# Lazy resolution
lazy_service = container.resolve_lazy(IExpensiveService)
```

## Lifetimes

| Lifetime | Description | Use Case |
|----------|-------------|----------|
| `Lifetime.SINGLETON` | One instance per container | Configuration, logging, caching |
| `Lifetime.TRANSIENT` | New instance every time | Stateful operations, lightweight objects |
| `Lifetime.SCOPED` | One instance per scope | Request handling, database connections |

## Scopes

```python
# Create scope
with container.create_scope() as scope:
    service = scope.resolve(IScopedService)
    # service is disposed when scope exits
```

## Constructor Injection

```python
class UserService:
    def __init__(self, repository: IUserRepository, logger: ILogger):
        self.repository = repository
        self.logger = logger

# Dependencies automatically injected
container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
container.register(IUserRepository, UserRepository, Lifetime.SCOPED)
container.register(UserService, UserService, Lifetime.TRANSIENT)

service = container.resolve(UserService)  # All dependencies injected!
```

## Error Handling

```python
from ai_automation_framework.core.di import ResolutionError, CircularDependencyError

try:
    service = container.resolve(IService)
except ResolutionError as e:
    print(f"Service not registered: {e}")
except CircularDependencyError as e:
    print(f"Circular dependency: {e}")
```

## Common Patterns

### Application Setup
```python
def configure_services() -> Container:
    container = Container()

    # Infrastructure
    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
    container.register(IConfig, AppConfig, Lifetime.SINGLETON)

    # Data Access
    container.register(IDatabase, Database, Lifetime.SCOPED)

    # Business Logic
    container.register(IUserService, UserService, Lifetime.TRANSIENT)

    return container
```

### Request Handling
```python
def handle_request(container: Container, request: Request) -> Response:
    with container.create_scope() as scope:
        scope.register_instance(Request, request)
        handler = scope.resolve(RequestHandler)
        return handler.handle()
```

### Testing
```python
def test_service():
    # Setup container
    container = Container()

    # Register mocks
    mock_repo = Mock(spec=IRepository)
    container.register_instance(IRepository, mock_repo)

    # Test
    service = container.resolve(IService)
    service.do_something()

    # Verify
    mock_repo.save.assert_called_once()
```

## Cheat Sheet

| Operation | Code |
|-----------|------|
| Create container | `Container()` |
| Register | `container.register(IService, Service, Lifetime.SINGLETON)` |
| Register instance | `container.register_instance(IService, instance)` |
| Register factory | `container.register_factory(IService, factory, Lifetime.SINGLETON)` |
| Resolve | `container.resolve(IService)` |
| Resolve named | `container.resolve(IService, name="primary")` |
| Lazy resolve | `container.resolve_lazy(IService)` |
| Create scope | `container.create_scope()` |
| Check registration | `container.is_registered(IService)` |
| Clear | `container.clear()` |

## See Also

- Full documentation: `/home/user/Automation_with_AI/docs/dependency_injection.md`
- Examples: `/home/user/Automation_with_AI/examples/di_container_example.py`
- Tests: `/home/user/Automation_with_AI/test_di_basic.py`

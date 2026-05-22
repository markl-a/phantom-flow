"""
Comprehensive example of using the Dependency Injection Container.

This example demonstrates:
1. Basic registration and resolution
2. Different lifetimes (singleton, transient, scoped)
3. Constructor injection
4. Factory functions
5. Named dependencies
6. Lazy resolution
7. Scoped containers
"""

from typing import Protocol, Optional
from ai_automation_framework.core.di import Container, Lifetime


# ============================================================================
# Example 1: Basic Service Registration
# ============================================================================

class IEmailService(Protocol):
    """Email service interface."""
    def send(self, to: str, subject: str, body: str) -> bool:
        ...


class SMTPEmailService:
    """SMTP implementation of email service."""

    def send(self, to: str, subject: str, body: str) -> bool:
        print(f"Sending email to {to}: {subject}")
        return True


def example_basic_registration():
    """Example of basic service registration."""
    print("\n=== Example 1: Basic Registration ===")

    container = Container()

    # Register service as singleton
    container.register(IEmailService, SMTPEmailService, Lifetime.SINGLETON)

    # Resolve service
    email_service = container.resolve(IEmailService)
    email_service.send("user@example.com", "Hello", "Test message")

    # Same instance due to singleton
    email_service2 = container.resolve(IEmailService)
    assert email_service is email_service2


# ============================================================================
# Example 2: Constructor Injection
# ============================================================================

class ILogger(Protocol):
    """Logger interface."""
    def log(self, message: str) -> None:
        ...


class ConsoleLogger:
    """Console logger implementation."""

    def log(self, message: str) -> None:
        print(f"[LOG] {message}")


class IConfig(Protocol):
    """Configuration interface."""
    def get(self, key: str) -> Optional[str]:
        ...


class AppConfig:
    """Application configuration."""

    def __init__(self):
        self._config = {
            "db_host": "localhost",
            "db_port": "5432",
            "db_name": "myapp"
        }

    def get(self, key: str) -> Optional[str]:
        return self._config.get(key)


class DatabaseConnection:
    """Database connection with injected dependencies."""

    def __init__(self, config: IConfig, logger: ILogger):
        """
        Initialize database connection.

        Args:
            config: Configuration service (injected)
            logger: Logger service (injected)
        """
        self.config = config
        self.logger = logger
        self.host = config.get("db_host")
        self.port = config.get("db_port")
        self.logger.log(f"Database connection initialized: {self.host}:{self.port}")

    def query(self, sql: str, params: tuple = ()) -> str:
        """Execute a parameterized query safely."""
        self.logger.log(f"Executing query: {sql} with params: {params}")
        return "Result"


def example_constructor_injection():
    """Example of automatic constructor injection."""
    print("\n=== Example 2: Constructor Injection ===")

    container = Container()

    # Register all dependencies
    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
    container.register(IConfig, AppConfig, Lifetime.SINGLETON)
    container.register(DatabaseConnection, DatabaseConnection, Lifetime.TRANSIENT)

    # Resolve - dependencies are automatically injected
    db = container.resolve(DatabaseConnection)
    db.query("SELECT * FROM users")


# ============================================================================
# Example 3: Factory Functions
# ============================================================================

class DatabasePool:
    """Database connection pool."""

    def __init__(self, size: int, logger: ILogger):
        self.size = size
        self.logger = logger
        self.logger.log(f"Creating connection pool with size {size}")

    def get_connection(self) -> DatabaseConnection:
        self.logger.log("Getting connection from pool")
        return DatabaseConnection(AppConfig(), self.logger)


def create_database_pool(container: Container) -> DatabasePool:
    """Factory function for creating database pool."""
    logger = container.resolve(ILogger)
    config = container.resolve(IConfig)
    pool_size = int(config.get("pool_size") or "10")
    return DatabasePool(pool_size, logger)


def example_factory_functions():
    """Example of using factory functions."""
    print("\n=== Example 3: Factory Functions ===")

    # Update config with pool size
    class AppConfigWithPool(AppConfig):
        def __init__(self):
            super().__init__()
            self._config["pool_size"] = "5"

    container = Container()
    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
    container.register(IConfig, AppConfigWithPool, Lifetime.SINGLETON)
    container.register_factory(DatabasePool, create_database_pool, Lifetime.SINGLETON)

    # Resolve - factory is called
    pool = container.resolve(DatabasePool)
    conn = pool.get_connection()


# ============================================================================
# Example 4: Named Dependencies
# ============================================================================

class CacheService:
    """Cache service."""

    def __init__(self, name: str):
        self.name = name

    def get(self, key: str) -> Optional[str]:
        return f"Value from {self.name}"


def example_named_dependencies():
    """Example of named dependencies."""
    print("\n=== Example 4: Named Dependencies ===")

    container = Container()

    # Register multiple implementations with names
    redis_cache = CacheService("Redis")
    memory_cache = CacheService("Memory")

    container.register_instance(CacheService, redis_cache, name="redis")
    container.register_instance(CacheService, memory_cache, name="memory")

    # Resolve by name
    cache1 = container.resolve(CacheService, name="redis")
    cache2 = container.resolve(CacheService, name="memory")

    print(f"Cache 1: {cache1.get('key1')}")
    print(f"Cache 2: {cache2.get('key2')}")


# ============================================================================
# Example 5: Lazy Resolution
# ============================================================================

class ExpensiveService:
    """Service with expensive initialization."""

    def __init__(self, logger: ILogger):
        self.logger = logger
        self.logger.log("ExpensiveService: Starting expensive initialization...")
        # Simulate expensive operation
        self.logger.log("ExpensiveService: Initialization complete")

    def do_work(self) -> str:
        self.logger.log("ExpensiveService: Doing work")
        return "Work done"


class WorkerService:
    """Service that may or may not need expensive service."""

    def __init__(self, logger: ILogger):
        self.logger = logger
        self._expensive_service: Optional[ExpensiveService] = None

    def set_expensive_service(self, service: ExpensiveService) -> None:
        self._expensive_service = service

    def quick_work(self) -> str:
        """Work that doesn't need expensive service."""
        self.logger.log("Doing quick work (no expensive service needed)")
        return "Quick work done"

    def heavy_work(self) -> str:
        """Work that needs expensive service."""
        if self._expensive_service is None:
            self.logger.log("ERROR: Expensive service not available")
            return "Error"
        return self._expensive_service.do_work()


def example_lazy_resolution():
    """Example of lazy resolution."""
    print("\n=== Example 5: Lazy Resolution ===")

    container = Container()
    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
    container.register(ExpensiveService, ExpensiveService, Lifetime.SINGLETON)

    # Create lazy proxy - service is NOT initialized yet
    logger = container.resolve(ILogger)
    logger.log("Creating lazy proxy...")
    lazy_service = container.resolve_lazy(ExpensiveService)
    logger.log("Lazy proxy created (service not initialized yet)")

    # Do some work without the service
    worker = WorkerService(logger)
    worker.quick_work()

    # Now use the lazy service - THIS triggers initialization
    logger.log("Now accessing lazy service...")
    worker.set_expensive_service(lazy_service)
    worker.heavy_work()


# ============================================================================
# Example 6: Scoped Containers
# ============================================================================

class RequestContext:
    """Request context with scoped lifetime."""

    def __init__(self, request_id: str, logger: ILogger):
        self.request_id = request_id
        self.logger = logger
        self.logger.log(f"Created request context: {request_id}")


class RequestHandler:
    """Handler that processes requests."""

    def __init__(self, context: RequestContext, logger: ILogger):
        self.context = context
        self.logger = logger

    def handle(self) -> str:
        self.logger.log(f"Handling request {self.context.request_id}")
        return f"Handled {self.context.request_id}"


def example_scoped_containers():
    """Example of scoped containers."""
    print("\n=== Example 6: Scoped Containers ===")

    # Create root container
    container = Container()
    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
    container.register(RequestContext, RequestContext, Lifetime.SCOPED)
    container.register(RequestHandler, RequestHandler, Lifetime.SCOPED)

    # Process first request with its own scope
    print("\n--- Request 1 ---")
    with container.create_scope() as scope1:
        # Register request-specific data
        scope1.register_instance(str, "request-001", name="request_id")

        # Create context with factory
        scope1.register_factory(
            RequestContext,
            lambda c: RequestContext(
                c.resolve(str, name="request_id"),
                c.resolve(ILogger)
            ),
            Lifetime.SCOPED
        )

        handler1 = scope1.resolve(RequestHandler)
        handler1.handle()

        # Resolving again in same scope returns same instance
        handler1_again = scope1.resolve(RequestHandler)
        assert handler1 is handler1_again

    # Process second request with different scope
    print("\n--- Request 2 ---")
    with container.create_scope() as scope2:
        scope2.register_instance(str, "request-002", name="request_id")

        scope2.register_factory(
            RequestContext,
            lambda c: RequestContext(
                c.resolve(str, name="request_id"),
                c.resolve(ILogger)
            ),
            Lifetime.SCOPED
        )

        handler2 = scope2.resolve(RequestHandler)
        handler2.handle()

        # Different scope = different instance
        assert handler1 is not handler2


# ============================================================================
# Example 7: Real-world Application Structure
# ============================================================================

class UserRepository:
    """Repository for user data."""

    def __init__(self, db: DatabaseConnection, logger: ILogger):
        self.db = db
        self.logger = logger

    def get_user(self, user_id: int) -> dict:
        self.logger.log(f"Getting user {user_id}")
        # Use parameterized query to prevent SQL injection
        result = self.db.query("SELECT * FROM users WHERE id = ?", (user_id,))
        return {"id": user_id, "name": "John Doe"}


class EmailNotificationService:
    """Service for sending email notifications."""

    def __init__(self, email: IEmailService, logger: ILogger):
        self.email = email
        self.logger = logger

    def notify_user(self, user: dict, message: str) -> bool:
        self.logger.log(f"Notifying user {user['name']}")
        return self.email.send(f"user_{user['id']}@example.com", "Notification", message)


class UserService:
    """High-level user service."""

    def __init__(
        self,
        repository: UserRepository,
        notifications: EmailNotificationService,
        logger: ILogger
    ):
        self.repository = repository
        self.notifications = notifications
        self.logger = logger

    def register_user(self, user_id: int) -> bool:
        self.logger.log(f"Registering user {user_id}")
        user = self.repository.get_user(user_id)
        return self.notifications.notify_user(user, "Welcome!")


def example_real_world_application():
    """Example of real-world application structure."""
    print("\n=== Example 7: Real-world Application ===")

    # Setup container with all dependencies
    container = Container()

    # Infrastructure
    container.register(ILogger, ConsoleLogger, Lifetime.SINGLETON)
    container.register(IConfig, AppConfig, Lifetime.SINGLETON)
    container.register(IEmailService, SMTPEmailService, Lifetime.SINGLETON)

    # Data access
    container.register(DatabaseConnection, DatabaseConnection, Lifetime.SCOPED)

    # Repositories
    container.register(UserRepository, UserRepository, Lifetime.SCOPED)

    # Services
    container.register(EmailNotificationService, EmailNotificationService, Lifetime.SINGLETON)
    container.register(UserService, UserService, Lifetime.SCOPED)

    # Use the application
    with container.create_scope() as scope:
        user_service = scope.resolve(UserService)
        user_service.register_user(123)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Dependency Injection Container - Comprehensive Examples")
    print("=" * 70)

    example_basic_registration()
    example_constructor_injection()
    example_factory_functions()
    example_named_dependencies()
    example_lazy_resolution()
    example_scoped_containers()
    example_real_world_application()

    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
